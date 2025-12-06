#!/usr/bin/env python3
"""
QUICK START: Optimist Farm Image Generator
==========================================

The simplest way to generate consistent storybook images.

SETUP (one time):
    pip install fal-client requests --break-system-packages
    export FAL_KEY="your-api-key-from-fal.ai"

USAGE:
    python quick_generate.py "your reference.jpg" "Barnaby exploring a cave"
"""

import sys
import os
import requests
from pathlib import Path
from datetime import datetime

try:
    import fal_client
except ImportError:
    print("Installing required packages...")
    os.system("pip install fal-client requests --break-system-packages")
    import fal_client


def generate(reference_image: str, scene_description: str, output_name: str = None):
    """
    Generate a single scene with your character.
    
    Args:
        reference_image: Path to your reference image (local file or URL)
        scene_description: What scene you want to create
        output_name: Optional custom filename (without extension)
    """
    
    # Check API key
    if not os.environ.get("FAL_KEY"):
        print("\n❌ FAL_KEY environment variable not set!")
        print("\nTo fix this:")
        print("1. Go to https://fal.ai and create an account")
        print("2. Get your API key from https://fal.ai/dashboard/keys")
        print("3. Run: export FAL_KEY='your-key-here'")
        print("4. Try again!\n")
        return None
    
    # Upload local image if needed
    if not reference_image.startswith("http"):
        path = Path(reference_image)
        if not path.exists():
            print(f"❌ File not found: {reference_image}")
            return None
        
        print(f"📤 Uploading {path.name}...")
        with open(path, "rb") as f:
            image_url = fal_client.upload(f.read(), content_type="image/jpeg")
    else:
        image_url = reference_image
    
    # Build the prompt
    prompt = f"""Keep the EXACT same characters, art style, and visual quality from the reference image.
    
New scene: {scene_description}

Maintain: Same character designs, clothing, fur textures, eye style, proportions, 3D animated style.
Quality: Children's storybook illustration, Pixar-quality, warm lighting, professional."""

    print(f"🎨 Generating: {scene_description[:50]}...")
    
    # Call the API
    try:
        result = fal_client.subscribe(
            "fal-ai/flux-pro/kontext",
            arguments={
                "prompt": prompt,
                "image_url": image_url,
                "guidance_scale": 3.5,
                "num_inference_steps": 28,
                "output_format": "jpeg",
            },
            with_logs=False
        )
    except Exception as e:
        print(f"❌ API Error: {e}")
        return None
    
    # Save the result
    result_url = result["images"][0]["url"]
    image_data = requests.get(result_url).content
    
    if output_name:
        filename = f"{output_name}.jpg"
    else:
        timestamp = datetime.now().strftime("%H%M%S")
        safe_desc = scene_description[:25].replace(" ", "_").replace(",", "")
        filename = f"optimist_farm_{safe_desc}_{timestamp}.jpg"
    
    output_dir = Path("./generated")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / filename
    
    with open(output_path, "wb") as f:
        f.write(image_data)
    
    print(f"✅ Saved: {output_path}")
    print(f"💰 Cost: ~$0.04")
    
    return str(output_path)


def batch_generate(reference_image: str, scenes: list, character_desc: str = ""):
    """
    Generate multiple scenes at once.
    
    Args:
        reference_image: Path to reference image
        scenes: List of scene descriptions
        character_desc: Optional character description for consistency
    """
    print(f"\n📚 Generating {len(scenes)} scenes...")
    print(f"💰 Estimated cost: ${len(scenes) * 0.04:.2f}\n")
    
    results = []
    for i, scene in enumerate(scenes, 1):
        print(f"\n[{i}/{len(scenes)}]")
        
        if character_desc:
            full_scene = f"{character_desc} - {scene}"
        else:
            full_scene = scene
            
        result = generate(
            reference_image,
            full_scene,
            output_name=f"scene_{i:02d}"
        )
        if result:
            results.append(result)
    
    print(f"\n✅ Complete! Generated {len(results)}/{len(scenes)} images")
    return results


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🐰 OPTIMIST FARM QUICK GENERATOR")
    print("="*50)
    
    if len(sys.argv) >= 3:
        # Direct command line usage
        ref_image = sys.argv[1]
        scene_desc = " ".join(sys.argv[2:])
        generate(ref_image, scene_desc)
    
    elif len(sys.argv) == 2 and sys.argv[1] == "--demo":
        # Demo mode
        print("\n📝 DEMO: Here's how to use this script:\n")
        print("Single image:")
        print('  python quick_generate.py "./my_reference.jpg" "Barnaby reading a book by candlelight"')
        print("\nIn Python:")
        print('''
from quick_generate import generate, batch_generate

# Single scene
generate("./characters.jpg", "The friends having a picnic in the meadow")

# Multiple scenes
scenes = [
    "Waking up at sunrise",
    "Eating breakfast together", 
    "Playing in the garden",
    "Finding a lost kitten",
    "Returning the kitten home",
    "Celebrating with cake"
]
batch_generate("./characters.jpg", scenes, "Barnaby Bunny and his farm friends")
''')
    
    else:
        print("\nUsage:")
        print("  python quick_generate.py <reference_image> <scene_description>")
        print("\nExample:")
        print('  python quick_generate.py "./farm_friends.jpg" "Characters having a birthday party"')
        print("\nFor demo code:")
        print("  python quick_generate.py --demo")
        print("\nSetup required:")
        print("  1. pip install fal-client requests --break-system-packages")
        print("  2. export FAL_KEY='your-key-from-fal.ai'")
