#!/usr/bin/env python3
"""
BOOK GENERATOR: Generate entire storybooks from config
=======================================================

Uses optimist_farm_config.json to generate all scenes for a book.

USAGE:
    python generate_book.py book_01_treasure_map
    python generate_book.py --list              # Show available books
    python generate_book.py --all               # Generate ALL books
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
import time

try:
    import fal_client
    import requests
except ImportError:
    print("Installing required packages...")
    os.system("pip install fal-client requests --break-system-packages")
    import fal_client
    import requests


class BookGenerator:
    """Generate complete storybooks from configuration."""
    
    def __init__(self, config_path: str = "./optimist_farm_config.json"):
        """Load configuration."""
        with open(config_path, "r") as f:
            self.config = json.load(f)
        
        self.style = self.config.get("style_description", "")
        self.characters = self.config.get("characters", {})
        self.books = self.config.get("books", {})
        self.locations = self.config.get("farm_locations", [])
        
        # Check API key
        if not os.environ.get("FAL_KEY"):
            print("\n❌ FAL_KEY not set!")
            print("Get your key: https://fal.ai/dashboard/keys")
            print("Then run: export FAL_KEY='your-key'\n")
            sys.exit(1)
    
    def list_books(self):
        """Show all available books."""
        print("\n📚 Available Books:")
        print("-" * 40)
        for book_id, book in self.books.items():
            chars = ", ".join(book.get("main_characters", []))
            scenes = len(book.get("scenes", []))
            print(f"  {book_id}")
            print(f"    Title: {book.get('title', 'Untitled')}")
            print(f"    Characters: {chars}")
            print(f"    Scenes: {scenes}")
            print(f"    Est. Cost: ${scenes * 0.04:.2f}")
            print()
    
    def list_characters(self):
        """Show all characters."""
        print("\n🐾 Characters:")
        print("-" * 40)
        for char_id, char in self.characters.items():
            print(f"  {char_id}: {char.get('name', 'Unknown')}")
            print(f"    {char.get('description', '')[:60]}...")
            print()
    
    def get_character_description(self, char_ids: list) -> str:
        """Build character description from IDs."""
        descriptions = []
        for char_id in char_ids:
            if char_id in self.characters:
                char = self.characters[char_id]
                descriptions.append(f"{char['name']}: {char['description']}")
        return "\n".join(descriptions)
    
    def get_combined_reference_image(self, char_ids: list) -> str:
        """Get the reference image for the main character."""
        # For now, use the first character's reference
        # In a more advanced version, you could stitch images together
        for char_id in char_ids:
            if char_id in self.characters:
                ref_path = self.characters[char_id].get("reference_image")
                if ref_path and Path(ref_path).exists():
                    return ref_path
        return None
    
    def generate_scene(
        self, 
        reference_url: str, 
        prompt: str, 
        characters_desc: str,
        output_path: Path
    ) -> bool:
        """Generate a single scene."""
        
        full_prompt = f"""Maintain these EXACT characters from the reference image:
{characters_desc}

Scene: {prompt}

Style: {self.style}
Keep: Same character designs, proportions, clothing, art style, 3D animated quality."""

        try:
            result = fal_client.subscribe(
                "fal-ai/flux-pro/kontext",
                arguments={
                    "prompt": full_prompt,
                    "image_url": reference_url,
                    "guidance_scale": 3.5,
                    "num_inference_steps": 28,
                    "output_format": "jpeg",
                },
                with_logs=False
            )
            
            # Download and save
            image_url = result["images"][0]["url"]
            image_data = requests.get(image_url).content
            
            with open(output_path, "wb") as f:
                f.write(image_data)
            
            return True
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            return False
    
    def generate_book(self, book_id: str, reference_image: str = None):
        """Generate all scenes for a book."""
        
        if book_id not in self.books:
            print(f"❌ Book not found: {book_id}")
            print("Use --list to see available books")
            return []
        
        book = self.books[book_id]
        title = book.get("title", book_id)
        char_ids = book.get("main_characters", [])
        scenes = book.get("scenes", [])
        
        print(f"\n📖 Generating: {title}")
        print(f"   {len(scenes)} scenes")
        print(f"   Estimated cost: ${len(scenes) * 0.04:.2f}")
        print("-" * 40)
        
        # Get character descriptions
        chars_desc = self.get_character_description(char_ids)
        
        # Get or upload reference image
        if reference_image:
            ref_path = reference_image
        else:
            ref_path = self.get_combined_reference_image(char_ids)
        
        if not ref_path:
            print("❌ No reference image found!")
            print("Please provide one: python generate_book.py book_id ./reference.jpg")
            return []
        
        print(f"📷 Using reference: {ref_path}")
        
        # Upload reference
        with open(ref_path, "rb") as f:
            ref_url = fal_client.upload(f.read(), content_type="image/jpeg")
        print("✓ Reference uploaded\n")
        
        # Create output directory
        output_dir = Path("./generated") / book_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate each scene
        results = []
        for scene in scenes:
            page_num = scene.get("page", len(results) + 1)
            prompt = scene.get("prompt", "")
            
            filename = f"page_{page_num:02d}.jpg"
            output_path = output_dir / filename
            
            print(f"[Page {page_num}] {prompt[:40]}...")
            
            success = self.generate_scene(ref_url, prompt, chars_desc, output_path)
            
            if success:
                print(f"    ✓ Saved: {output_path}")
                results.append(str(output_path))
            
            # Rate limiting
            time.sleep(1)
        
        print(f"\n✅ Complete! {len(results)}/{len(scenes)} pages generated")
        print(f"📁 Output: {output_dir}")
        
        return results


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python generate_book.py <book_id> [reference_image]")
        print("  python generate_book.py --list")
        print("  python generate_book.py --characters")
        print("\nExamples:")
        print("  python generate_book.py book_01_treasure_map")
        print("  python generate_book.py book_01_treasure_map ./my_reference.jpg")
        sys.exit(0)
    
    generator = BookGenerator()
    
    if sys.argv[1] == "--list":
        generator.list_books()
    
    elif sys.argv[1] == "--characters":
        generator.list_characters()
    
    elif sys.argv[1] == "--all":
        print("⚠️  This will generate ALL books. Are you sure?")
        confirm = input("Type 'yes' to continue: ")
        if confirm.lower() == "yes":
            ref_image = sys.argv[2] if len(sys.argv) > 2 else None
            for book_id in generator.books.keys():
                generator.generate_book(book_id, ref_image)
    
    else:
        book_id = sys.argv[1]
        ref_image = sys.argv[2] if len(sys.argv) > 2 else None
        generator.generate_book(book_id, ref_image)
