#!/usr/bin/env python3
"""
Optimist Farm Image Generator Engine
====================================
Core generation engine for creating character references, group shots,
book scenes, and covers using Flux Kontext API.

All settings are configurable via the config manager.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    import fal_client
except ImportError:
    print("Installing fal-client...")
    os.system("pip install fal-client requests --break-system-packages")
    import fal_client

from config_manager import ConfigManager, get_config, Character, Location, Book


@dataclass
class GenerationResult:
    """Result of an image generation."""
    success: bool
    output_path: Optional[str] = None
    image_url: Optional[str] = None  # Direct URL from fal.ai (for serverless)
    prompt_used: str = ""
    error: Optional[str] = None
    cost: float = 0.04
    generation_time: float = 0.0
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def is_serverless():
    """Check if running in a serverless environment (Vercel, AWS Lambda, etc.)."""
    return os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME')


class OptimistFarmGenerator:
    """
    Main generator class for Optimist Farm illustrations.

    Supports:
    - Hero shots (single character references)
    - Group shots (multiple characters)
    - Scene generation (story pages)
    - Book covers
    - Batch generation

    All parameters are configurable via ConfigManager.
    """

    def __init__(self, config: Optional[ConfigManager] = None, save_to_disk: bool = None):
        """
        Initialize generator.

        Args:
            config: ConfigManager instance. Uses default if not provided.
            save_to_disk: Whether to save images to disk. Auto-detected if None.
        """
        self.config = config or get_config()
        self._check_api_key()
        self._uploaded_images: Dict[str, str] = {}  # Cache for uploaded image URLs

        # Auto-detect if we should save to disk (disabled in serverless)
        if save_to_disk is None:
            self.save_to_disk = not is_serverless()
        else:
            self.save_to_disk = save_to_disk

    def _check_api_key(self) -> None:
        """Check if API key is set."""
        if not os.environ.get("FAL_KEY"):
            print("\n" + "="*50)
            print("FAL_KEY environment variable not set!")
            print("="*50)
            print("\nTo fix this:")
            print("1. Go to https://fal.ai and create an account")
            print("2. Get your API key from https://fal.ai/dashboard/keys")
            print("3. Run: export FAL_KEY='your-key-here'")
            print("4. Try again!")
            print("="*50 + "\n")

    def _ensure_directory(self, path: Path) -> Path:
        """Ensure directory exists."""
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _upload_image(self, image_path: str, force: bool = False) -> str:
        """
        Upload a local image to get a URL for the API.

        Args:
            image_path: Path to local image
            force: Force re-upload even if cached

        Returns:
            URL of uploaded image
        """
        if image_path.startswith("http"):
            return image_path

        # Check cache
        if not force and image_path in self._uploaded_images:
            return self._uploaded_images[image_path]

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        print(f"  Uploading: {path.name}...")
        with open(path, "rb") as f:
            url = fal_client.upload(f.read(), content_type="image/jpeg")

        self._uploaded_images[image_path] = url
        return url

    def _call_api(
        self,
        prompt: str,
        reference_url: Optional[str] = None,
        guidance_scale: Optional[float] = None,
        num_steps: Optional[int] = None
    ) -> Dict:
        """
        Call the Flux Kontext API.

        Args:
            prompt: Generation prompt
            reference_url: URL of reference image (required for consistency)
            guidance_scale: Override guidance scale
            num_steps: Override inference steps

        Returns:
            API response dictionary
        """
        defaults = self.config.api_defaults

        arguments = {
            "prompt": prompt,
            "guidance_scale": guidance_scale or defaults.get("guidance_scale", 3.5),
            "num_inference_steps": num_steps or defaults.get("num_inference_steps", 28),
            "output_format": defaults.get("output_format", "jpeg"),
        }

        if reference_url:
            arguments["image_url"] = reference_url

        result = fal_client.subscribe(
            self.config.api_model,
            arguments=arguments,
            with_logs=False
        )

        return result

    def _save_image(
        self,
        image_url: str,
        output_path: Path,
        save_prompt: bool = True,
        prompt: str = ""
    ) -> str:
        """
        Download and save image from URL.

        Args:
            image_url: URL of generated image
            output_path: Path to save to
            save_prompt: Whether to save prompt alongside image
            prompt: The prompt used for generation

        Returns:
            Path to saved image
        """
        # Download image
        image_data = requests.get(image_url).content

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save image
        with open(output_path, "wb") as f:
            f.write(image_data)

        # Optionally save prompt
        if save_prompt and prompt and self.config.generation_settings.get("save_prompts", True):
            prompt_path = output_path.with_suffix(".txt")
            with open(prompt_path, "w") as f:
                f.write(prompt)

        return str(output_path)

    def _get_aspect_ratio_dims(self, ratio_type: str) -> Tuple[int, int]:
        """
        Get dimensions for an aspect ratio.

        Note: Flux Kontext doesn't directly support aspect ratios,
        but we track this for documentation and potential cropping.

        Args:
            ratio_type: Type of ratio (hero, scene, cover, group)

        Returns:
            Tuple of (width, height)
        """
        ratio_str = self.config.image_settings.get_ratio(ratio_type)

        # Parse ratio string
        if ":" in ratio_str:
            w, h = map(int, ratio_str.split(":"))
        else:
            w, h = 1, 1

        # Scale to reasonable dimensions
        base = 1024
        if w > h:
            return (base, int(base * h / w))
        elif h > w:
            return (int(base * w / h), base)
        else:
            return (base, base)

    # =========================================================================
    # Hero Shot Generation
    # =========================================================================

    def generate_hero_shot(
        self,
        character_id: str,
        reference_image: Optional[str] = None,
        location_id: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        output_name: Optional[str] = None
    ) -> GenerationResult:
        """
        Generate a hero shot (reference image) for a character.

        Args:
            character_id: ID of character to generate
            reference_image: Optional reference image for style/consistency
            location_id: Optional location for background context
            custom_prompt: Override the default prompt
            output_name: Custom output filename

        Returns:
            GenerationResult with path to generated image
        """
        start_time = time.time()

        # Get character
        character = self.config.get_character(character_id)
        if not character:
            return GenerationResult(
                success=False,
                error=f"Character not found: {character_id}"
            )

        # Get optional location
        location = None
        location_desc = "soft, neutral background"
        if location_id:
            location = self.config.get_location(location_id)
            if location:
                location_desc = location.description

        # Build prompt
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = self.config.build_prompt(
                "hero_shot",
                character_name=character.name,
                character_description=character.description,
                location=location_desc,
                style_prompt=self.config.active_style_prompt
            )

        print(f"\nGenerating hero shot: {character.name}")
        print(f"  Style: {self.config.active_style}")

        try:
            # Upload reference if provided
            ref_url = None
            if reference_image:
                ref_url = self._upload_image(reference_image)

            # Call API
            result = self._call_api(prompt, ref_url)

            # Get the generated image URL
            image_url = result["images"][0]["url"]
            generation_time = time.time() - start_time
            saved_path = None

            # Save to disk if not in serverless environment
            if self.save_to_disk:
                output_dir = Path(self.config.paths.get("character_references", "./reference_images/characters"))
                char_dir = self._ensure_directory(output_dir / character_id)

                if output_name:
                    filename = f"{output_name}.jpg"
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"hero_{timestamp}.jpg"

                output_path = char_dir / filename
                saved_path = self._save_image(image_url, output_path, prompt=prompt)
                print(f"  Saved: {saved_path}")

            print(f"  Time: {generation_time:.1f}s | Cost: ${self.config.cost_per_image}")

            return GenerationResult(
                success=True,
                output_path=saved_path,
                image_url=image_url,
                prompt_used=prompt,
                cost=self.config.cost_per_image,
                generation_time=generation_time,
                metadata={
                    "character_id": character_id,
                    "character_name": character.name,
                    "type": "hero_shot"
                }
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                error=str(e),
                prompt_used=prompt
            )

    def generate_all_hero_shots(
        self,
        reference_image: Optional[str] = None,
        character_ids: Optional[List[str]] = None
    ) -> List[GenerationResult]:
        """
        Generate hero shots for all (or specified) characters.

        Args:
            reference_image: Optional reference for style consistency
            character_ids: Optional list of specific characters to generate

        Returns:
            List of GenerationResults
        """
        ids_to_generate = character_ids or self.config.list_character_ids()

        print(f"\nGenerating {len(ids_to_generate)} hero shots...")
        print(f"Estimated cost: ${len(ids_to_generate) * self.config.cost_per_image:.2f}")

        results = []
        for i, char_id in enumerate(ids_to_generate, 1):
            print(f"\n[{i}/{len(ids_to_generate)}]")
            result = self.generate_hero_shot(char_id, reference_image)
            results.append(result)

            # Rate limiting
            if i < len(ids_to_generate):
                delay = self.config.generation_settings.get("rate_limit_delay_seconds", 1)
                time.sleep(delay)

        # Summary
        successful = sum(1 for r in results if r.success)
        total_cost = sum(r.cost for r in results if r.success)
        print(f"\nComplete: {successful}/{len(ids_to_generate)} generated")
        print(f"Total cost: ${total_cost:.2f}")

        return results

    # =========================================================================
    # Group Shot Generation
    # =========================================================================

    def generate_group_shot(
        self,
        character_ids: List[str],
        reference_image: Optional[str] = None,
        location_id: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        output_name: Optional[str] = None
    ) -> GenerationResult:
        """
        Generate a group shot with multiple characters.

        Args:
            character_ids: List of character IDs to include
            reference_image: Reference image for consistency
            location_id: Optional location for background
            custom_prompt: Override default prompt
            output_name: Custom output filename

        Returns:
            GenerationResult
        """
        start_time = time.time()

        # Get characters
        characters = []
        for char_id in character_ids:
            char = self.config.get_character(char_id)
            if char:
                characters.append(char)

        if not characters:
            return GenerationResult(
                success=False,
                error="No valid characters found"
            )

        # Build character list and descriptions
        char_names = [c.name for c in characters]
        char_list = ", ".join(char_names)
        char_descriptions = "\n".join([f"- {c.name}: {c.description}" for c in characters])

        # Get location
        location_desc = "beautiful farm setting with rolling hills"
        if location_id:
            location = self.config.get_location(location_id)
            if location:
                location_desc = location.description

        # Build prompt
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = self.config.build_prompt(
                "group_shot",
                character_list=char_list,
                character_descriptions=char_descriptions,
                location_description=location_desc,
                style_prompt=self.config.active_style_prompt
            )

        print(f"\nGenerating group shot: {char_list}")

        try:
            # Upload reference if provided
            ref_url = None
            if reference_image:
                ref_url = self._upload_image(reference_image)

            # Call API
            result = self._call_api(prompt, ref_url)

            # Get the generated image URL
            image_url = result["images"][0]["url"]
            generation_time = time.time() - start_time
            saved_path = None

            # Save to disk if not in serverless environment
            if self.save_to_disk:
                output_dir = Path(self.config.paths.get("group_shots", "./reference_images/group_shots"))
                output_dir = self._ensure_directory(output_dir)

                if output_name:
                    filename = f"{output_name}.jpg"
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    char_abbrev = "_".join([c[:3] for c in character_ids[:4]])
                    filename = f"group_{char_abbrev}_{timestamp}.jpg"

                output_path = output_dir / filename
                saved_path = self._save_image(image_url, output_path, prompt=prompt)
                print(f"  Saved: {saved_path}")

            print(f"  Time: {generation_time:.1f}s | Cost: ${self.config.cost_per_image}")

            return GenerationResult(
                success=True,
                output_path=saved_path,
                image_url=image_url,
                prompt_used=prompt,
                cost=self.config.cost_per_image,
                generation_time=generation_time,
                metadata={
                    "character_ids": character_ids,
                    "character_names": char_names,
                    "type": "group_shot"
                }
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                error=str(e),
                prompt_used=prompt
            )

    # =========================================================================
    # Scene Generation
    # =========================================================================

    def generate_scene(
        self,
        scene_prompt: str,
        character_ids: List[str],
        reference_image: str,
        location_id: Optional[str] = None,
        output_name: Optional[str] = None,
        additional_notes: str = ""
    ) -> GenerationResult:
        """
        Generate a scene/page illustration.

        Args:
            scene_prompt: Description of what's happening in the scene
            character_ids: Characters appearing in the scene
            reference_image: Reference image for character consistency
            location_id: Optional location ID for setting
            output_name: Custom output filename
            additional_notes: Extra instructions for the prompt

        Returns:
            GenerationResult
        """
        start_time = time.time()

        # Get characters
        characters = [self.config.get_character(cid) for cid in character_ids]
        characters = [c for c in characters if c]

        char_list = ", ".join([c.name for c in characters])
        char_descriptions = self.config.get_character_description_block(character_ids)

        # Get location
        location_desc = ""
        if location_id:
            location = self.config.get_location(location_id)
            if location:
                location_desc = location.description

        # Build prompt
        prompt = self.config.build_prompt(
            "scene",
            scene_description=scene_prompt,
            character_list=char_list,
            character_descriptions=char_descriptions,
            location_description=location_desc,
            additional_notes=additional_notes,
            style_prompt=self.config.active_style_prompt
        )

        # Add consistency suffix
        consistency = self.config.get_prompt_template("consistency_suffix")
        if consistency:
            prompt += f"\n\n{consistency}"

        print(f"\nGenerating scene: {scene_prompt[:50]}...")

        try:
            # Upload reference
            ref_url = self._upload_image(reference_image)

            # Call API
            result = self._call_api(prompt, ref_url)

            # Get the generated image URL
            image_url = result["images"][0]["url"]
            generation_time = time.time() - start_time
            saved_path = None

            # Save to disk if not in serverless environment
            if self.save_to_disk:
                output_dir = Path(self.config.paths.get("output", "./output"))
                output_dir = self._ensure_directory(output_dir)

                if output_name:
                    filename = f"{output_name}.jpg"
                else:
                    timestamp = datetime.now().strftime("%H%M%S")
                    safe_prompt = scene_prompt[:25].replace(" ", "_").replace(",", "")
                    filename = f"scene_{safe_prompt}_{timestamp}.jpg"

                output_path = output_dir / filename
                saved_path = self._save_image(image_url, output_path, prompt=prompt)
                print(f"  Saved: {saved_path}")

            print(f"  Time: {generation_time:.1f}s | Cost: ${self.config.cost_per_image}")

            return GenerationResult(
                success=True,
                output_path=saved_path,
                image_url=image_url,
                prompt_used=prompt,
                cost=self.config.cost_per_image,
                generation_time=generation_time,
                metadata={
                    "scene_prompt": scene_prompt,
                    "character_ids": character_ids,
                    "type": "scene"
                }
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                error=str(e),
                prompt_used=prompt
            )

    # =========================================================================
    # Book Cover Generation
    # =========================================================================

    def generate_cover(
        self,
        book_id: str,
        reference_image: str,
        custom_prompt: Optional[str] = None,
        output_name: Optional[str] = None
    ) -> GenerationResult:
        """
        Generate a book cover.

        Args:
            book_id: ID of the book
            reference_image: Reference image for character consistency
            custom_prompt: Override default prompt
            output_name: Custom output filename

        Returns:
            GenerationResult
        """
        start_time = time.time()

        # Get book
        book = self.config.get_book(book_id)
        if not book:
            return GenerationResult(
                success=False,
                error=f"Book not found: {book_id}"
            )

        # Get featured character
        featured = self.config.get_character(book.featured_character)
        if not featured:
            return GenerationResult(
                success=False,
                error=f"Featured character not found: {book.featured_character}"
            )

        # Get location
        location = self.config.get_location(book.primary_location)
        location_desc = location.description if location else "beautiful farm setting"

        # Build prompt
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = self.config.build_prompt(
                "cover",
                book_title=book.title,
                virtue=book.virtue,
                featured_character_name=featured.name,
                featured_character_description=featured.description,
                location_description=location_desc,
                style_prompt=self.config.active_style_prompt
            )

        print(f"\nGenerating cover: {book.title}")
        print(f"  Featured: {featured.name}")

        try:
            # Upload reference
            ref_url = self._upload_image(reference_image)

            # Call API
            result = self._call_api(prompt, ref_url)

            # Get the generated image URL
            image_url = result["images"][0]["url"]
            generation_time = time.time() - start_time
            saved_path = None

            # Save to disk if not in serverless environment
            if self.save_to_disk:
                output_dir = Path(self.config.paths.get("covers_output", "./output/covers"))
                output_dir = self._ensure_directory(output_dir)

                if output_name:
                    filename = f"{output_name}.jpg"
                else:
                    filename = f"cover_{book_id}.jpg"

                output_path = output_dir / filename
                saved_path = self._save_image(image_url, output_path, prompt=prompt)
                print(f"  Saved: {saved_path}")

            print(f"  Time: {generation_time:.1f}s | Cost: ${self.config.cost_per_image}")

            return GenerationResult(
                success=True,
                output_path=saved_path,
                image_url=image_url,
                prompt_used=prompt,
                cost=self.config.cost_per_image,
                generation_time=generation_time,
                metadata={
                    "book_id": book_id,
                    "book_title": book.title,
                    "type": "cover"
                }
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                error=str(e),
                prompt_used=prompt
            )

    # =========================================================================
    # Book Generation (All Pages)
    # =========================================================================

    def generate_book(
        self,
        book_id: str,
        reference_image: str,
        include_cover: bool = True,
        page_range: Optional[Tuple[int, int]] = None
    ) -> List[GenerationResult]:
        """
        Generate all pages for a book.

        Args:
            book_id: ID of the book to generate
            reference_image: Reference image for consistency
            include_cover: Whether to generate cover
            page_range: Optional (start, end) page range

        Returns:
            List of GenerationResults
        """
        # Get book
        book = self.config.get_book(book_id)
        if not book:
            print(f"Book not found: {book_id}")
            return []

        scenes = book.scenes
        if not scenes:
            print(f"No scenes defined for book: {book_id}")
            print("Add scenes to the book configuration first.")
            return []

        # Filter by page range if specified
        if page_range:
            start, end = page_range
            scenes = [s for s in scenes if start <= s.get("page", 0) <= end]

        # Calculate totals
        total_images = len(scenes) + (1 if include_cover else 0)
        total_cost = total_images * self.config.cost_per_image

        print(f"\n{'='*50}")
        print(f"GENERATING BOOK: {book.title}")
        print(f"{'='*50}")
        print(f"Virtue: {book.virtue}")
        print(f"Featured: {book.featured_character}")
        print(f"Pages: {len(scenes)}")
        print(f"Include cover: {include_cover}")
        print(f"Estimated cost: ${total_cost:.2f}")
        print(f"{'='*50}")

        results = []

        # Get all character IDs for this book
        all_char_ids = [book.featured_character] + book.supporting_characters

        # Create output directory
        output_dir = Path(self.config.paths.get("books_output", "./output/books")) / book_id
        self._ensure_directory(output_dir)

        # Generate cover
        if include_cover:
            print("\n[Cover]")
            cover_result = self.generate_cover(
                book_id,
                reference_image,
                output_name=str(output_dir / "cover")
            )
            results.append(cover_result)
            time.sleep(self.config.generation_settings.get("rate_limit_delay_seconds", 1))

        # Generate scenes
        for i, scene in enumerate(scenes, 1):
            page_num = scene.get("page", i)
            scene_prompt = scene.get("prompt", "")
            scene_chars = scene.get("characters", all_char_ids)

            print(f"\n[Page {page_num}/{len(scenes)}]")
            print(f"  {scene_prompt[:50]}...")

            result = self.generate_scene(
                scene_prompt=scene_prompt,
                character_ids=scene_chars,
                reference_image=reference_image,
                location_id=book.primary_location,
                output_name=str(output_dir / f"page_{page_num:02d}")
            )
            results.append(result)

            # Rate limiting
            if i < len(scenes):
                time.sleep(self.config.generation_settings.get("rate_limit_delay_seconds", 1))

        # Summary
        successful = sum(1 for r in results if r.success)
        actual_cost = sum(r.cost for r in results if r.success)

        print(f"\n{'='*50}")
        print(f"COMPLETE: {book.title}")
        print(f"{'='*50}")
        print(f"Generated: {successful}/{len(results)} images")
        print(f"Total cost: ${actual_cost:.2f}")
        print(f"Output: {output_dir}")
        print(f"{'='*50}\n")

        return results

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def estimate_cost(self, num_images: int) -> float:
        """Estimate cost for generating N images."""
        return num_images * self.config.cost_per_image

    def list_generated_images(self, output_type: str = "all") -> List[Path]:
        """
        List all generated images.

        Args:
            output_type: Filter by type (all, characters, groups, books, covers)

        Returns:
            List of image paths
        """
        paths = self.config.paths
        search_dirs = []

        if output_type in ("all", "characters"):
            search_dirs.append(Path(paths.get("character_references", "./reference_images/characters")))
        if output_type in ("all", "groups"):
            search_dirs.append(Path(paths.get("group_shots", "./reference_images/group_shots")))
        if output_type in ("all", "books"):
            search_dirs.append(Path(paths.get("books_output", "./output/books")))
        if output_type in ("all", "covers"):
            search_dirs.append(Path(paths.get("covers_output", "./output/covers")))

        images = []
        for dir_path in search_dirs:
            if dir_path.exists():
                images.extend(dir_path.rglob("*.jpg"))
                images.extend(dir_path.rglob("*.jpeg"))
                images.extend(dir_path.rglob("*.png"))

        return sorted(images)


# =============================================================================
# Convenience Functions
# =============================================================================

_generator: Optional[OptimistFarmGenerator] = None

def get_generator(config: Optional[ConfigManager] = None) -> OptimistFarmGenerator:
    """Get generator instance (singleton pattern)."""
    global _generator
    if _generator is None or config:
        _generator = OptimistFarmGenerator(config)
    return _generator


# =============================================================================
# CLI Testing
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("OPTIMIST FARM GENERATOR - Test Mode")
    print("="*60)

    try:
        generator = OptimistFarmGenerator()

        print("\nGenerator initialized successfully!")
        print(f"API Model: {generator.config.api_model}")
        print(f"Active Style: {generator.config.active_style}")
        print(f"Cost per image: ${generator.config.cost_per_image}")

        print("\nAvailable characters:")
        for char in generator.config.list_characters()[:5]:
            print(f"  - {char['name']}")
        print(f"  ... and {len(generator.config.list_characters()) - 5} more")

        print("\nTo generate images, use the CLI:")
        print("  python generate.py hero barnaby_bunny")
        print("  python generate.py group barnaby_bunny,gus_goat,christy_cow")
        print("  python generate.py cover book_01_courage --ref ./reference.jpg")

    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Make sure you're running from the project root directory.")
