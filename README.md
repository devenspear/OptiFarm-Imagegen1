# Optimist Farm Storybook Generator v2.0

AI-powered children's storybook illustration generator based on the Optimist Farm Writing Bible v2.4.

Generate consistent character references, group shots, scene illustrations, and book covers for your storybook series using Flux Kontext API.

## Live Demo

**Web App**: [https://optifarm-imagegen1.vercel.app](https://optifarm-imagegen1.vercel.app)

**GitHub**: [https://github.com/devenspear/OptiFarm-Imagegen1](https://github.com/devenspear/OptiFarm-Imagegen1)

---

## Features

- **Web UI** - Beautiful Flask-based interface for easy image generation
- **17 Pre-configured Characters** from Writing Bible v2.4 (Ollie, Barnaby, Pearl, Gus, etc.)
- **13 Books** with virtues framework (Courage, Empathy, Teamwork, etc.)
- **10 Locations** (Garden, Barn, Pond, Meadow, etc.)
- **4 Style Presets** (Saturated Rainbow, Pixar, Watercolor, Cartoon)
- **Fully Configurable** - all settings in JSON, update anytime
- **Multiple Generation Modes**: Hero shots, group shots, scenes, covers, full books
- **Serverless Ready** - Works on Vercel, AWS Lambda, and locally
- **Low Cost**: ~$0.04 per image via fal.ai

---

## Web UI

The easiest way to use the generator is through the web interface:

### Local Development

```bash
# Install dependencies
pip install flask fal-client requests

# Set API key
export FAL_KEY="your-api-key-from-fal.ai"

# Run the web app
python3 web_app.py

# Open http://localhost:8080
```

### Vercel Deployment

The app is pre-configured for Vercel deployment:

1. Fork or clone the repository
2. Connect to Vercel
3. Add `FAL_KEY` environment variable in Vercel settings
4. Deploy

---

## Quick Start (CLI)

### 1. Install Dependencies

```bash
pip install fal-client requests --break-system-packages
```

### 2. Set API Key

```bash
# Get your key from https://fal.ai/dashboard/keys
export FAL_KEY="your-api-key-here"
```

### 3. Explore Available Content

```bash
# List all characters
python3 generate.py list characters

# List all books
python3 generate.py list books

# List all styles
python3 generate.py list styles

# View configuration summary
python3 generate.py config --summary
```

### 4. Generate Images

```bash
# Generate a hero shot for a character
python3 generate.py hero barnaby_bunny

# Generate a group shot
python3 generate.py group barnaby_bunny,gus_goat,christy_cow --ref ./reference.jpg

# Generate a book cover
python3 generate.py cover book_01_courage --ref ./reference.jpg

# Generate an entire book
python3 generate.py book book_01_courage --ref ./reference.jpg
```

---

## Important: Reference Images

Flux Kontext is an **image-to-image model**. You must provide a reference image URL for all generations.

**Supported URL sources:**
- Direct image URLs (ending in .jpg, .png, etc.)
- Imgur
- Cloudinary
- Any public image host

**NOT supported:**
- Google Drive links
- Dropbox links (unless using `dl=1`)
- OneDrive links

---

## Project Structure

```
OptiFarm-ImageGenerator1.0/
├── web_app.py                     # Flask web application
├── generate.py                    # Main CLI entry point
├── config/
│   └── master_config.json         # All settings, characters, books, styles
├── src/
│   ├── __init__.py
│   ├── config_manager.py          # Configuration loading and management
│   └── generator.py               # Core image generation engine
├── templates/                     # Flask HTML templates
│   ├── base.html
│   ├── index.html
│   ├── generate.html
│   ├── characters.html
│   ├── books.html
│   └── gallery.html
├── reference_images/
│   ├── characters/                # Character hero shots (generated)
│   ├── group_shots/               # Group reference images
│   └── style_references/          # Style guide images
├── output/
│   ├── books/                     # Generated book pages
│   └── covers/                    # Generated covers
├── vercel.json                    # Vercel deployment config
├── requirements.txt               # Python dependencies
└── ReferenceDocs/                 # Writing Bible, Strategic Playbook
```

---

## CLI Reference

### Generate Hero Shots (Character References)

```bash
# Single character
python3 generate.py hero barnaby_bunny

# With reference for style consistency
python3 generate.py hero barnaby_bunny --ref ./style_reference.jpg

# All characters at once
python3 generate.py hero --all

# Specific subset of characters
python3 generate.py hero --all --characters barnaby_bunny,gus_goat,pearl_pig
```

### Generate Group Shots

```bash
# Basic group shot
python3 generate.py group barnaby_bunny,gus_goat,christy_cow --ref ./reference.jpg

# With specific location
python3 generate.py group barnaby_bunny,gus_goat --ref ./ref.jpg --location meadow

# Custom output name
python3 generate.py group barnaby_bunny,pearl_pig --ref ./ref.jpg --output team_leaders
```

### Generate Scenes

```bash
python3 generate.py scene \
  --prompt "Barnaby and friends discovering a treasure map in the barn" \
  --characters barnaby_bunny,gus_goat,christy_cow \
  --ref ./reference.jpg \
  --location barn
```

### Generate Book Covers

```bash
# Generate cover for a book
python3 generate.py cover book_01_courage --ref ./reference.jpg

# Custom output name
python3 generate.py cover book_01_courage --ref ./ref.jpg --output courage_cover_v2
```

### Generate Entire Books

```bash
# Full book with cover
python3 generate.py book book_01_courage --ref ./reference.jpg

# Without cover
python3 generate.py book book_01_courage --ref ./ref.jpg --no-cover

# Specific page range
python3 generate.py book book_01_courage --ref ./ref.jpg --pages 1-5
```

### Configuration Management

```bash
# View summary
python3 generate.py config --summary

# Get a specific value
python3 generate.py config --get active_style
python3 generate.py config --get api.defaults.guidance_scale

# Set a value
python3 generate.py config --set active_style=pixar
python3 generate.py config --set api.defaults.guidance_scale=4.0

# Change style preset
python3 generate.py config --style watercolor

# Export configuration
python3 generate.py config --export ./backup_config.json
```

### List Available Items

```bash
python3 generate.py list characters   # All 17 characters
python3 generate.py list books        # All 13 books
python3 generate.py list locations    # All 10 locations
python3 generate.py list styles       # All 4 style presets
python3 generate.py list all          # Everything
```

---

## Characters (17 total)

### Core Cast (9)
| ID | Name | Role | Primary Virtue |
|----|------|------|----------------|
| ollie_owl | Ollie the Owl | Mentor | Wisdom |
| barnaby_bunny | Barnaby Bunny | Core | Gratitude |
| pearl_pig | Pearl the Pig | Core | Perseverance |
| gus_goat | Gus the Goat | Core | Self-Control |
| christy_cow | Christy the Cow | Core | Kindness |
| lillie_lamb | Lillie the Lamb | Core | Patience |
| dugan_dog | Dugan the Dog | Core | Trust |
| clementine_chick | Clementine the Chick | Core | Honesty |
| delilah_duck | Delilah the Duck | Core | Responsibility |

### Friends (7)
| ID | Name | Primary Virtue |
|----|------|----------------|
| dixie_duckling | Dixie the Duckling | Courage |
| lil_dax_donkey | Lil Dax the Donkey | Helpfulness |
| posie_piglet | Posie the Piglet | Friendship |
| snip_squirrel | Snip the Squirrel | Sharing |
| millie_mouse | Millie the Mouse | Empathy |
| hollis_horse | Hollis the Horse | Optimism |
| ralphie_rooster | Ralphie the Rooster | Fairness |

### Special
| ID | Name | Function |
|----|------|----------|
| pippin_snail | Pippin the Snail | Seek-and-find on every page |

---

## Books (13 total)

| # | ID | Title | Virtue | Featured |
|---|----|----|--------|----------|
| 1 | book_01_courage | One Brave Step | Courage | Dixie |
| 2 | book_02_empathy | I See You, I'm Here | Empathy | Millie |
| 3 | book_03_self_control | Wait, Breathe, Then Go | Self-Control | Gus |
| 4 | book_04_friendship_snip | Better With Two | Friendship | Snip |
| 5 | book_05_friendship_posie | Friends Make Fun | Friendship | Posie |
| 6 | book_06_helpfulness | Helping Hands Are Happy Hands | Helpfulness | Lil Dax |
| 7 | book_07_teamwork_pearl | We Pull Together | Teamwork | Pearl |
| 8 | book_08_teamwork_gus | Together Is Stronger | Teamwork | Gus |
| 9 | book_09_forgiveness | Let's Start New | Forgiveness | Christy |
| 10 | book_10_optimism | Look for the Good | Optimism | Hollis |
| 11 | book_11_fairness | Fair Is Share | Fairness | Ralphie |
| 12 | book_12_trust | I Know You're There | Trust | Dugan |
| 13 | book_13_compassion | Be Gentle, Be Kind | Compassion | Lillie |

---

## Style Presets

| ID | Name | Description |
|----|------|-------------|
| default | Saturated Rainbow | Bright, optimistic, rainbow-forward (Writing Bible v2.4) |
| pixar | Pixar-Quality 3D | Soft textures, warm lighting, high detail |
| watercolor | Soft Watercolor | Gentle, muted, Beatrix Potter inspired |
| cartoon | Vibrant Cartoon | Clean lines, bright colors, animation style |

Change style:
```bash
python3 generate.py config --style pixar
```

---

## Configuration

All settings are stored in `config/master_config.json`. Key sections:

### API Settings
```json
{
  "api": {
    "provider": "fal-ai",
    "model": "fal-ai/flux-pro/kontext",
    "defaults": {
      "guidance_scale": 3.5,
      "num_inference_steps": 28,
      "output_format": "jpeg"
    },
    "cost_per_image": 0.04
  }
}
```

### Image Settings
```json
{
  "image_settings": {
    "aspect_ratios": {
      "square": "1:1",
      "landscape": "3:2",
      "portrait": "2:3"
    },
    "hero_shot_ratio": "square",
    "scene_ratio": "landscape",
    "cover_ratio": "portrait"
  }
}
```

### Adding Book Scenes
Edit `config/master_config.json` and add scenes to any book:
```json
{
  "books": {
    "book_01_courage": {
      "scenes": [
        {"page": 1, "prompt": "Dixie at the pond, looking nervous at the big lily pad"},
        {"page": 2, "prompt": "Ollie appears with wisdom, soft glow around him"},
        {"page": 3, "prompt": "Dixie takes her first brave hop onto the lily pad"}
      ]
    }
  }
}
```

---

## Python API Usage

```python
from src import get_config, get_generator

# Load configuration
config = get_config()

# Create generator
generator = get_generator(config)

# Generate hero shot
result = generator.generate_hero_shot(
    "barnaby_bunny",
    reference_image="./reference.jpg"
)
print(f"Image URL: {result.image_url}")
print(f"Saved to: {result.output_path}")

# Generate group shot
result = generator.generate_group_shot(
    character_ids=["barnaby_bunny", "gus_goat", "christy_cow"],
    reference_image="./reference.jpg",
    location_id="meadow"
)

# Generate scene
result = generator.generate_scene(
    scene_prompt="Friends celebrating in the garden at sunset",
    character_ids=["barnaby_bunny", "pearl_pig"],
    reference_image="./reference.jpg",
    location_id="garden"
)

# Generate book cover
result = generator.generate_cover(
    book_id="book_01_courage",
    reference_image="./reference.jpg"
)

# Generate entire book
results = generator.generate_book(
    book_id="book_01_courage",
    reference_image="./reference.jpg"
)
```

---

## Cost Estimates

| Generation Type | Images | Cost |
|-----------------|--------|------|
| Single hero shot | 1 | $0.04 |
| All hero shots (17 chars) | 17 | $0.68 |
| Group shot | 1 | $0.04 |
| Book cover | 1 | $0.04 |
| Book (8 pages + cover) | 9 | $0.36 |
| Full series (13 books) | ~130 | $5.20 |

---

## Troubleshooting

**"FAL_KEY not set"**
```bash
export FAL_KEY="your-key-from-fal.ai"
```

**"Config file not found"**
```bash
# Run from project root directory
cd /path/to/OptiFarm-ImageGenerator1.0
python3 generate.py list characters
```

**"Google Drive links not supported"**
Google Drive, Dropbox, and OneDrive links don't work with fal.ai. Upload your reference image to Imgur, Cloudinary, or another direct image host.

**"Read-only file system" (Vercel)**
This is handled automatically. The app returns the fal.ai image URL directly instead of saving to disk.

**"No scenes defined for book"**
Add scenes to the book in `config/master_config.json`

**Characters not consistent**
- Use a clearer reference image
- Increase guidance_scale: `python3 generate.py config --set api.defaults.guidance_scale=4.0`
- Add more detail to character descriptions in config

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| FAL_KEY | fal.ai API key | Yes |
| VERCEL | Auto-set by Vercel (enables serverless mode) | Auto |

---

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Add `FAL_KEY` environment variable
4. Deploy

### Local Development

```bash
pip install -r requirements.txt
export FAL_KEY="your-key"
python3 web_app.py
```

---

## Legacy Scripts

The original scripts are still available for simple use cases:
- `quick_generate.py` - Single image generation
- `generate_book.py` - Basic book generation
- `optimist_farm_toolkit/` - Previous toolkit version

---

## Reference Documents

- `ReferenceDocs/Optimist Farm Series 2 — Writing Bible v2.4.md` - Character and story guidelines
- `ReferenceDocs/Optimist Farm_ Strategic Playbook 2.0.md` - Business and brand strategy
- `ReferenceDocs/Example-BookImagePrompts.md` - Example scene prompts

---

## Version History

- **v2.1** - Added Web UI, Vercel deployment, serverless support
- **v2.0** - Full rewrite with configurable system, 17 characters, 13 books, CLI interface
- **v1.0** - Original toolkit with basic generation

---

## License

Private - Optimist Farm is a registered trademark.
