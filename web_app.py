#!/usr/bin/env python3
"""
Optimist Farm Web UI
====================
Flask-based web interface for the Optimist Farm Image Generator.

Run with: python3 web_app.py
Then open: http://localhost:5000
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory

# Load .env file if it exists
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_manager import ConfigManager, get_config
from generator import OptimistFarmGenerator, get_generator, GenerationResult

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Global instances
config = None
generator = None

def init_app():
    """Initialize config and generator."""
    global config, generator
    try:
        config = get_config()
        generator = get_generator(config)
        return True
    except Exception as e:
        print(f"Error initializing: {e}")
        return False

# ============================================================================
# Routes - Pages
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html',
                          characters=config.list_characters(),
                          books=config.list_books(),
                          locations=config.list_locations(),
                          styles=config.list_styles(),
                          active_style=config.active_style,
                          api_key_set=bool(os.environ.get("FAL_KEY")))

@app.route('/characters')
def characters_page():
    """Characters listing page."""
    characters_data = []
    for char_id in config.list_character_ids():
        char = config.get_character(char_id)
        if char:
            characters_data.append({
                'id': char.id,
                'name': char.name,
                'role': char.role,
                'description': char.description,
                'personality': char.personality,
                'visual_cues': char.visual_cues,
                'virtues': char.virtues,
                'reference_image': char.reference_image
            })
    return render_template('characters.html', characters=characters_data)

@app.route('/books')
def books_page():
    """Books listing page."""
    books_data = []
    for book_id in config.list_book_ids():
        book = config.get_book(book_id)
        if book:
            featured = config.get_character(book.featured_character)
            books_data.append({
                'id': book.id,
                'title': book.title,
                'book_number': book.book_number,
                'virtue': book.virtue,
                'featured_character': book.featured_character,
                'featured_name': featured.name if featured else '',
                'supporting_characters': book.supporting_characters,
                'primary_location': book.primary_location,
                'mantra': book.mantra,
                'micro_ritual': book.micro_ritual,
                'scenes_count': len(book.scenes)
            })
    return render_template('books.html', books=sorted(books_data, key=lambda x: x['book_number']))

@app.route('/generate')
def generate_page():
    """Generation interface page."""
    return render_template('generate.html',
                          characters=config.list_characters(),
                          books=config.list_books(),
                          locations=config.list_locations(),
                          styles=config.list_styles(),
                          active_style=config.active_style)

@app.route('/gallery')
def gallery_page():
    """Generated images gallery."""
    images = []

    # Collect all generated images
    for img_type in ['characters', 'groups', 'books', 'covers']:
        for img_path in generator.list_generated_images(img_type):
            # Check for associated prompt file
            prompt_path = img_path.with_suffix('.txt')
            prompt = ""
            if prompt_path.exists():
                prompt = prompt_path.read_text()[:200]

            images.append({
                'path': str(img_path),
                'filename': img_path.name,
                'type': img_type,
                'prompt': prompt,
                'url': f'/images/{img_path.relative_to(Path.cwd())}'
            })

    return render_template('gallery.html', images=images)

# ============================================================================
# Routes - API Endpoints
# ============================================================================

@app.route('/api/config')
def api_config():
    """Get current configuration."""
    return jsonify({
        'project': config.project_name,
        'active_style': config.active_style,
        'characters_count': len(config.list_characters()),
        'books_count': len(config.list_books()),
        'locations_count': len(config.list_locations()),
        'cost_per_image': config.cost_per_image,
        'api_key_set': bool(os.environ.get("FAL_KEY"))
    })

@app.route('/api/characters')
def api_characters():
    """Get all characters."""
    characters = []
    for char_id in config.list_character_ids():
        char = config.get_character(char_id)
        if char:
            characters.append({
                'id': char.id,
                'name': char.name,
                'role': char.role,
                'description': char.description,
                'virtues': char.virtues
            })
    return jsonify(characters)

@app.route('/api/books')
def api_books():
    """Get all books."""
    return jsonify(config.list_books())

@app.route('/api/locations')
def api_locations():
    """Get all locations."""
    locations = []
    for loc_id in config.list_location_ids():
        loc = config.get_location(loc_id)
        if loc:
            locations.append({
                'id': loc.id,
                'name': loc.name,
                'description': loc.description
            })
    return jsonify(locations)

@app.route('/api/styles')
def api_styles():
    """Get all style presets."""
    return jsonify({
        'styles': config.list_styles(),
        'active': config.active_style
    })

@app.route('/api/style', methods=['POST'])
def api_set_style():
    """Set active style."""
    data = request.json
    style_id = data.get('style_id')
    if config.set_active_style(style_id):
        config.save()
        return jsonify({'success': True, 'active_style': style_id})
    return jsonify({'success': False, 'error': 'Style not found'}), 400

@app.route('/api/generate/hero', methods=['POST'])
def api_generate_hero():
    """Generate a hero shot."""
    if not os.environ.get("FAL_KEY"):
        return jsonify({'success': False, 'error': 'FAL_KEY not set'}), 400

    data = request.json
    character_id = data.get('character_id')
    reference_image = data.get('reference_image')
    location_id = data.get('location_id')

    if not character_id:
        return jsonify({'success': False, 'error': 'character_id required'}), 400

    result = generator.generate_hero_shot(
        character_id=character_id,
        reference_image=reference_image,
        location_id=location_id
    )

    return jsonify({
        'success': result.success,
        'output_path': result.output_path,
        'cost': result.cost,
        'error': result.error
    })

@app.route('/api/generate/group', methods=['POST'])
def api_generate_group():
    """Generate a group shot."""
    if not os.environ.get("FAL_KEY"):
        return jsonify({'success': False, 'error': 'FAL_KEY not set'}), 400

    data = request.json
    character_ids = data.get('character_ids', [])
    reference_image = data.get('reference_image')
    location_id = data.get('location_id')

    if not character_ids:
        return jsonify({'success': False, 'error': 'character_ids required'}), 400

    result = generator.generate_group_shot(
        character_ids=character_ids,
        reference_image=reference_image,
        location_id=location_id
    )

    return jsonify({
        'success': result.success,
        'output_path': result.output_path,
        'cost': result.cost,
        'error': result.error
    })

@app.route('/api/generate/scene', methods=['POST'])
def api_generate_scene():
    """Generate a scene."""
    if not os.environ.get("FAL_KEY"):
        return jsonify({'success': False, 'error': 'FAL_KEY not set'}), 400

    data = request.json
    scene_prompt = data.get('prompt')
    character_ids = data.get('character_ids', [])
    reference_image = data.get('reference_image')
    location_id = data.get('location_id')

    if not scene_prompt:
        return jsonify({'success': False, 'error': 'prompt required'}), 400
    if not reference_image:
        return jsonify({'success': False, 'error': 'reference_image required'}), 400

    result = generator.generate_scene(
        scene_prompt=scene_prompt,
        character_ids=character_ids,
        reference_image=reference_image,
        location_id=location_id
    )

    return jsonify({
        'success': result.success,
        'output_path': result.output_path,
        'cost': result.cost,
        'error': result.error
    })

@app.route('/api/generate/cover', methods=['POST'])
def api_generate_cover():
    """Generate a book cover."""
    if not os.environ.get("FAL_KEY"):
        return jsonify({'success': False, 'error': 'FAL_KEY not set'}), 400

    data = request.json
    book_id = data.get('book_id')
    reference_image = data.get('reference_image')

    if not book_id:
        return jsonify({'success': False, 'error': 'book_id required'}), 400
    if not reference_image:
        return jsonify({'success': False, 'error': 'reference_image required'}), 400

    result = generator.generate_cover(
        book_id=book_id,
        reference_image=reference_image
    )

    return jsonify({
        'success': result.success,
        'output_path': result.output_path,
        'cost': result.cost,
        'error': result.error
    })

@app.route('/api/estimate', methods=['POST'])
def api_estimate_cost():
    """Estimate generation cost."""
    data = request.json
    num_images = data.get('num_images', 1)
    return jsonify({
        'num_images': num_images,
        'estimated_cost': generator.estimate_cost(num_images)
    })

# ============================================================================
# Routes - Static Files
# ============================================================================

@app.route('/images/<path:filepath>')
def serve_image(filepath):
    """Serve generated images."""
    return send_from_directory('.', filepath)

# ============================================================================
# Main
# ============================================================================

# Initialize on import for Vercel
init_app()

if __name__ == '__main__':
    print("\n" + "="*50)
    print("OPTIMIST FARM WEB UI")
    print("="*50)

    if config:
        print(f"Config loaded: {config.project_name}")
        print(f"Characters: {len(config.list_characters())}")
        print(f"Books: {len(config.list_books())}")
        print(f"API Key: {'Set' if os.environ.get('FAL_KEY') else 'NOT SET'}")
        print("="*50)
        print("\nStarting server at http://localhost:8080")
        print("Press Ctrl+C to stop\n")

        app.run(debug=True, host='0.0.0.0', port=8080)
    else:
        print("Failed to initialize. Check config file exists.")
