#!/usr/bin/env python3
"""
Optimist Farm Storybook Image Generator
========================================
Generates consistent character images for children's storybooks using Flux Kontext API.

Setup:
1. pip install fal-client Pillow requests --break-system-packages
2. Get your API key from https://fal.ai/dashboard/keys
3. Set environment variable: export FAL_KEY="your-api-key-here"

Usage:
    python optimist_farm_generator.py

Cost: ~$0.04 per image via fal.ai
"""

import os
import json
import base64
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional
import time

# Check for fal_client
try:
    import fal_client
except ImportError:
    print("Installing fal-client...")
    os.system("pip install fal-client Pillow requests --break-system-packages")
    import fal_client


class OptimistFarmGenerator:
    """Generate consistent storybook illustrations using Flux Kontext."""
    
    # Style prompt to maintain the 3D animated look
    STYLE_PROMPT = """3D animated children's storybook illustration style, 
    Pixar-quality rendering, soft fur textures, expressive cartoon eyes, 
    warm natural lighting, shallow depth of field, whimsical farm setting, 
    high detail, professional children's book quality"""
    
    def __init__(self, output_dir: str = "./optimist_farm_output"):
        """Initialize the generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for API key
        if not os.environ.get("FAL_KEY"):
            print("\n⚠️  FAL_KEY not set!")
            print("Get your key from: https://fal.ai/dashboard/keys")
            print("Then run: export FAL_KEY='your-key-here'\n")
    
    def upload_image(self, image_path: str) -> str:
        """Upload a local image and get a URL for the API."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Read and encode the image
        with open(path, "rb") as f:
            image_data = f.read()
        
        # Upload to fal's CDN
        url = fal_client.upload(image_data, content_type="image/jpeg")
        print(f"✓ Uploaded: {path.name}")
        return url
    
    def generate_scene(
        self,
        reference_image: str,
        scene_prompt: str,
        character_description: str = "",
        output_name: Optional[str] = None,
        guidance_scale: float = 3.5,
        num_steps: int = 28
    ) -> str:
        """
        Generate a new scene with consistent characters.
        
        Args:
            reference_image: Path to reference image OR URL
            scene_prompt: Description of the new scene
            character_description: Who/what to keep consistent (e.g., "Barnaby Bunny in blue overalls")
            output_name: Custom name for output file
            guidance_scale: How closely to follow the prompt (2.0-5.0, default 3.5)
            num_steps: Quality steps (more = better but slower)
        
        Returns:
            Path to the generated image
        """
        # Upload if it's a local file
        if not reference_image.startswith("http"):
            image_url = self.upload_image(reference_image)
        else:
            image_url = reference_image
        
        # Build the full prompt
        full_prompt = f"""Using the exact same character(s) and art style from the reference image:
{character_description}

New scene: {scene_prompt}

Maintain: exact same character appearance, clothing, fur texture, eye style, proportions.
Style: {self.STYLE_PROMPT}"""
        
        print(f"\n🎨 Generating: {scene_prompt[:50]}...")
        
        # Call the Flux Kontext API
        result = fal_client.subscribe(
            "fal-ai/flux-pro/kontext",
            arguments={
                "prompt": full_prompt,
                "image_url": image_url,
                "guidance_scale": guidance_scale,
                "num_inference_steps": num_steps,
                "output_format": "jpeg",
            },
            with_logs=False
        )
        
        # Download and save the result
        image_url = result["images"][0]["url"]
        image_data = requests.get(image_url).content
        
        # Generate output filename
        if output_name:
            filename = f"{output_name}.jpg"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_prompt = scene_prompt[:30].replace(" ", "_").replace(",", "")
            filename = f"scene_{safe_prompt}_{timestamp}.jpg"
        
        output_path = self.output_dir / filename
        with open(output_path, "wb") as f:
            f.write(image_data)
        
        print(f"✓ Saved: {output_path}")
        return str(output_path)
    
    def generate_book_scenes(
        self,
        reference_image: str,
        scenes: list[dict],
        character_description: str = ""
    ) -> list[str]:
        """
        Generate multiple scenes for a storybook.
        
        Args:
            reference_image: Path to your character reference image
            scenes: List of dicts with 'prompt' and optional 'name' keys
            character_description: Description of character(s) to maintain
        
        Returns:
            List of paths to generated images
        
        Example:
            scenes = [
                {"prompt": "waking up in the barn at sunrise", "name": "page_01"},
                {"prompt": "eating breakfast with friends", "name": "page_02"},
                {"prompt": "playing in the meadow", "name": "page_03"},
            ]
        """
        output_paths = []
        
        # Upload reference once
        if not reference_image.startswith("http"):
            image_url = self.upload_image(reference_image)
        else:
            image_url = reference_image
        
        print(f"\n📚 Generating {len(scenes)} scenes...")
        print(f"   Estimated cost: ${len(scenes) * 0.04:.2f}\n")
        
        for i, scene in enumerate(scenes, 1):
            prompt = scene.get("prompt", "")
            name = scene.get("name", f"scene_{i:02d}")
            
            print(f"[{i}/{len(scenes)}] {prompt[:40]}...")
            
            try:
                path = self.generate_scene(
                    reference_image=image_url,
                    scene_prompt=prompt,
                    character_description=character_description,
                    output_name=name
                )
                output_paths.append(path)
                
                # Small delay to avoid rate limiting
                if i < len(scenes):
                    time.sleep(1)
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
        
        print(f"\n✅ Generated {len(output_paths)}/{len(scenes)} images")
        print(f"📁 Output folder: {self.output_dir}")
        
        return output_paths


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Initialize the generator
    generator = OptimistFarmGenerator(output_dir="./optimist_farm_output")
    
    # Example 1: Single scene generation
    print("\n" + "="*60)
    print("OPTIMIST FARM STORYBOOK GENERATOR")
    print("="*60)
    
    # Define your characters
    CHARACTERS = """
    Barnaby Bunny: Gray and white bunny wearing blue denim overalls with plaid shirt
    Goat: Tan colored goat with spiral horns and beard
    Cow: Black and white spotted Holstein calf, cheerful expression
    """
    
    # Example scenes for a story
    example_scenes = [
        {
            "prompt": "The three friends waking up at sunrise, stretching in the barn, golden morning light streaming through wooden slats",
            "name": "book1_page01_sunrise"
        },
        {
            "prompt": "Barnaby Bunny discovering a mysterious treasure map in the hay loft, excited expression, dusty attic setting",
            "name": "book1_page02_discovery"
        },
        {
            "prompt": "All three characters gathered around a wooden table, looking at the treasure map together, afternoon light",
            "name": "book1_page03_planning"
        },
        {
            "prompt": "The friends walking through a beautiful flower meadow, butterflies around them, blue sky with fluffy clouds",
            "name": "book1_page04_adventure"
        },
        {
            "prompt": "Characters crossing a small wooden bridge over a babbling brook, reflections in the water",
            "name": "book1_page05_bridge"
        },
        {
            "prompt": "Finding the treasure chest under a large oak tree, expressions of joy and surprise",
            "name": "book1_page06_treasure"
        },
        {
            "prompt": "The three friends hugging and celebrating, sunset colors, the farm visible in the background",
            "name": "book1_page07_celebration"
        },
        {
            "prompt": "Walking back to the farm together at twilight, fireflies glowing around them",
            "name": "book1_page08_homeward"
        },
    ]
    
    print("\n📖 Example Book: 'The Treasure Map Adventure'")
    print(f"   {len(example_scenes)} scenes defined")
    print(f"   Estimated cost: ${len(example_scenes) * 0.04:.2f}")
    
    print("\n" + "-"*60)
    print("To generate images, run this script with your reference image:")
    print("-"*60)
    print("""
# Option 1: Interactive single scene
generator.generate_scene(
    reference_image="./your_reference_image.jpg",
    scene_prompt="Barnaby Bunny reading a book by candlelight in the barn",
    character_description="Barnaby Bunny in blue overalls, the goat, and the spotted cow"
)

# Option 2: Generate entire book
generator.generate_book_scenes(
    reference_image="./your_reference_image.jpg",
    scenes=example_scenes,
    character_description=CHARACTERS
)
""")
    
    # Uncomment to run with your actual image:
    # generator.generate_book_scenes(
    #     reference_image="/path/to/your/optimist_farm_reference.jpg",
    #     scenes=example_scenes,
    #     character_description=CHARACTERS
    # )
