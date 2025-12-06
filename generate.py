#!/usr/bin/env python3
"""
Optimist Farm Image Generator CLI
=================================
Command-line interface for generating Optimist Farm illustrations.

Usage:
    python generate.py <command> [options]

Commands:
    hero        Generate character hero shot (reference image)
    group       Generate group shot with multiple characters
    scene       Generate a scene/page illustration
    cover       Generate a book cover
    book        Generate all pages for a book
    config      View and modify configuration
    list        List available characters, locations, books, styles

Examples:
    python generate.py hero barnaby_bunny
    python generate.py hero --all
    python generate.py group barnaby_bunny,gus_goat,christy_cow
    python generate.py cover book_01_courage --ref ./reference.jpg
    python generate.py book book_01_courage --ref ./reference.jpg
    python generate.py list characters
    python generate.py config --set active_style pixar
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_manager import ConfigManager, get_config
from generator import OptimistFarmGenerator, get_generator


def cmd_hero(args, generator: OptimistFarmGenerator):
    """Generate hero shot(s)."""
    if args.all:
        # Generate all characters
        char_ids = args.characters.split(",") if args.characters else None
        results = generator.generate_all_hero_shots(
            reference_image=args.ref,
            character_ids=char_ids
        )
        return len([r for r in results if r.success])
    else:
        if not args.character_id:
            print("Error: Specify a character ID or use --all")
            print("Example: python generate.py hero barnaby_bunny")
            print("         python generate.py hero --all")
            return 0

        result = generator.generate_hero_shot(
            character_id=args.character_id,
            reference_image=args.ref,
            location_id=args.location,
            output_name=args.output
        )

        if result.success:
            print(f"\nSuccess! Image saved to: {result.output_path}")
            return 1
        else:
            print(f"\nError: {result.error}")
            return 0


def cmd_group(args, generator: OptimistFarmGenerator):
    """Generate group shot."""
    if not args.character_ids:
        print("Error: Specify character IDs separated by commas")
        print("Example: python generate.py group barnaby_bunny,gus_goat,christy_cow")
        return 0

    char_ids = [c.strip() for c in args.character_ids.split(",")]

    result = generator.generate_group_shot(
        character_ids=char_ids,
        reference_image=args.ref,
        location_id=args.location,
        output_name=args.output
    )

    if result.success:
        print(f"\nSuccess! Image saved to: {result.output_path}")
        return 1
    else:
        print(f"\nError: {result.error}")
        return 0


def cmd_scene(args, generator: OptimistFarmGenerator):
    """Generate a scene."""
    if not args.prompt:
        print("Error: Specify a scene prompt with --prompt")
        print('Example: python generate.py scene --prompt "Barnaby watering the garden at sunrise"')
        return 0

    if not args.ref:
        print("Error: Scene generation requires a reference image with --ref")
        return 0

    char_ids = []
    if args.characters:
        char_ids = [c.strip() for c in args.characters.split(",")]

    result = generator.generate_scene(
        scene_prompt=args.prompt,
        character_ids=char_ids,
        reference_image=args.ref,
        location_id=args.location,
        output_name=args.output
    )

    if result.success:
        print(f"\nSuccess! Image saved to: {result.output_path}")
        return 1
    else:
        print(f"\nError: {result.error}")
        return 0


def cmd_cover(args, generator: OptimistFarmGenerator):
    """Generate book cover."""
    if not args.book_id:
        print("Error: Specify a book ID")
        print("Example: python generate.py cover book_01_courage --ref ./reference.jpg")
        print("\nAvailable books:")
        for book in generator.config.list_books():
            print(f"  {book['id']}: {book['title']}")
        return 0

    if not args.ref:
        print("Error: Cover generation requires a reference image with --ref")
        return 0

    result = generator.generate_cover(
        book_id=args.book_id,
        reference_image=args.ref,
        output_name=args.output
    )

    if result.success:
        print(f"\nSuccess! Cover saved to: {result.output_path}")
        return 1
    else:
        print(f"\nError: {result.error}")
        return 0


def cmd_book(args, generator: OptimistFarmGenerator):
    """Generate entire book."""
    if not args.book_id:
        print("Error: Specify a book ID")
        print("Example: python generate.py book book_01_courage --ref ./reference.jpg")
        print("\nAvailable books:")
        for book in generator.config.list_books():
            print(f"  {book['id']}: {book['title']}")
        return 0

    if not args.ref:
        print("Error: Book generation requires a reference image with --ref")
        return 0

    # Parse page range if provided
    page_range = None
    if args.pages:
        parts = args.pages.split("-")
        if len(parts) == 2:
            page_range = (int(parts[0]), int(parts[1]))

    results = generator.generate_book(
        book_id=args.book_id,
        reference_image=args.ref,
        include_cover=not args.no_cover,
        page_range=page_range
    )

    return len([r for r in results if r.success])


def cmd_list(args, config: ConfigManager):
    """List available items."""
    item_type = args.item_type or "all"

    if item_type in ("all", "characters"):
        print("\n=== CHARACTERS ===")
        for char in config.list_characters():
            print(f"  {char['id']:<20} {char['name']:<25} ({char['role']})")

    if item_type in ("all", "locations"):
        print("\n=== LOCATIONS ===")
        for loc in config.list_locations():
            print(f"  {loc['id']:<20} {loc['name']}")

    if item_type in ("all", "books"):
        print("\n=== BOOKS ===")
        for book in config.list_books():
            print(f"  {book['id']:<25} Book {book['number']:>2}: {book['title']}")
            print(f"  {'':<25} Virtue: {book['virtue']}, Featured: {book['featured_character']}")

    if item_type in ("all", "styles"):
        print("\n=== STYLES ===")
        active = config.active_style
        for style in config.list_styles():
            marker = "*" if style['id'] == active else " "
            print(f"  {marker} {style['id']:<15} {style['name']}")

    print()


def cmd_config(args, config: ConfigManager):
    """View or modify configuration."""
    if args.summary:
        config.print_summary()
        return

    if args.get:
        value = config.get_value(args.get)
        print(f"{args.get} = {value}")
        return

    if args.set:
        key, value = args.set.split("=", 1)
        # Try to parse as JSON, otherwise use as string
        try:
            import json
            value = json.loads(value)
        except:
            pass
        config.set_value(key.strip(), value)
        config.save()
        print(f"Set {key.strip()} = {value}")
        return

    if args.style:
        if config.set_active_style(args.style):
            config.save()
            print(f"Active style set to: {args.style}")
        else:
            print(f"Style not found: {args.style}")
            print("Available styles:")
            for style in config.list_styles():
                print(f"  - {style['id']}")
        return

    if args.export:
        import json
        output_path = args.export
        with open(output_path, "w") as f:
            json.dump(config.export_config(), f, indent=2)
        print(f"Config exported to: {output_path}")
        return

    # Default: show summary
    config.print_summary()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Optimist Farm Image Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate.py hero barnaby_bunny
  python generate.py hero --all --ref ./style_reference.jpg
  python generate.py group barnaby_bunny,gus_goat,christy_cow --ref ./ref.jpg
  python generate.py scene --prompt "Friends playing in meadow" --characters barnaby_bunny,gus_goat --ref ./ref.jpg
  python generate.py cover book_01_courage --ref ./reference.jpg
  python generate.py book book_01_courage --ref ./reference.jpg
  python generate.py list characters
  python generate.py config --style pixar
        """
    )

    parser.add_argument("--config", "-c", help="Path to config file", default=None)

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Hero command
    hero_parser = subparsers.add_parser("hero", help="Generate character hero shot")
    hero_parser.add_argument("character_id", nargs="?", help="Character ID to generate")
    hero_parser.add_argument("--all", "-a", action="store_true", help="Generate all characters")
    hero_parser.add_argument("--characters", help="Comma-separated character IDs (with --all)")
    hero_parser.add_argument("--ref", "-r", help="Reference image for style consistency")
    hero_parser.add_argument("--location", "-l", help="Location ID for background")
    hero_parser.add_argument("--output", "-o", help="Output filename (without extension)")

    # Group command
    group_parser = subparsers.add_parser("group", help="Generate group shot")
    group_parser.add_argument("character_ids", nargs="?", help="Comma-separated character IDs")
    group_parser.add_argument("--ref", "-r", help="Reference image for style consistency")
    group_parser.add_argument("--location", "-l", help="Location ID for background")
    group_parser.add_argument("--output", "-o", help="Output filename")

    # Scene command
    scene_parser = subparsers.add_parser("scene", help="Generate scene illustration")
    scene_parser.add_argument("--prompt", "-p", required=True, help="Scene description")
    scene_parser.add_argument("--characters", help="Comma-separated character IDs")
    scene_parser.add_argument("--ref", "-r", required=True, help="Reference image (required)")
    scene_parser.add_argument("--location", "-l", help="Location ID")
    scene_parser.add_argument("--output", "-o", help="Output filename")

    # Cover command
    cover_parser = subparsers.add_parser("cover", help="Generate book cover")
    cover_parser.add_argument("book_id", nargs="?", help="Book ID")
    cover_parser.add_argument("--ref", "-r", required=True, help="Reference image (required)")
    cover_parser.add_argument("--output", "-o", help="Output filename")

    # Book command
    book_parser = subparsers.add_parser("book", help="Generate entire book")
    book_parser.add_argument("book_id", nargs="?", help="Book ID")
    book_parser.add_argument("--ref", "-r", required=True, help="Reference image (required)")
    book_parser.add_argument("--pages", help="Page range (e.g., 1-5)")
    book_parser.add_argument("--no-cover", action="store_true", help="Skip cover generation")

    # List command
    list_parser = subparsers.add_parser("list", help="List available items")
    list_parser.add_argument("item_type", nargs="?",
                            choices=["characters", "locations", "books", "styles", "all"],
                            default="all", help="What to list")

    # Config command
    config_parser = subparsers.add_parser("config", help="View/modify configuration")
    config_parser.add_argument("--summary", "-s", action="store_true", help="Show config summary")
    config_parser.add_argument("--get", help="Get a config value (dot notation)")
    config_parser.add_argument("--set", help="Set a config value (key=value)")
    config_parser.add_argument("--style", help="Set active style preset")
    config_parser.add_argument("--export", help="Export config to file")

    args = parser.parse_args()

    # Show help if no command
    if not args.command:
        parser.print_help()
        print("\n" + "="*50)
        print("Quick Start:")
        print("="*50)
        print("1. Set your API key: export FAL_KEY='your-key'")
        print("2. List characters: python generate.py list characters")
        print("3. Generate hero: python generate.py hero barnaby_bunny")
        print("="*50)
        return

    # Load config
    try:
        config = get_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nMake sure you're running from the project root directory.")
        print("Or specify config path: python generate.py --config /path/to/config.json")
        return

    # Handle list and config commands (don't need generator)
    if args.command == "list":
        cmd_list(args, config)
        return

    if args.command == "config":
        cmd_config(args, config)
        return

    # For generation commands, create generator
    generator = get_generator(config)

    # Check API key for generation commands
    if not os.environ.get("FAL_KEY"):
        print("\n" + "="*50)
        print("ERROR: FAL_KEY environment variable not set!")
        print("="*50)
        print("\nTo fix this:")
        print("1. Go to https://fal.ai and create an account")
        print("2. Get your API key from https://fal.ai/dashboard/keys")
        print("3. Run: export FAL_KEY='your-key-here'")
        print("4. Try again!")
        print("="*50 + "\n")
        return

    # Execute command
    if args.command == "hero":
        cmd_hero(args, generator)
    elif args.command == "group":
        cmd_group(args, generator)
    elif args.command == "scene":
        cmd_scene(args, generator)
    elif args.command == "cover":
        cmd_cover(args, generator)
    elif args.command == "book":
        cmd_book(args, generator)


if __name__ == "__main__":
    main()
