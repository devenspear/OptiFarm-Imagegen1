# 🐰 Optimist Farm Storybook Generator

Generate consistent AI character illustrations for your children's storybook series using Flux Kontext.

## ✨ Features

- **Character Consistency**: Same characters across unlimited scenes
- **No Training Required**: Just provide a reference image
- **Batch Generation**: Generate entire books automatically
- **Low Cost**: ~$0.04 per image
- **Simple Setup**: 3 commands to get started

---

## 🚀 Quick Start (5 minutes)

### 1. Install Dependencies

```bash
pip install fal-client requests --break-system-packages
```

### 2. Get Your API Key

1. Go to [fal.ai](https://fal.ai)
2. Create a free account
3. Get your key from [Dashboard → Keys](https://fal.ai/dashboard/keys)
4. Set the environment variable:

```bash
export FAL_KEY="your-api-key-here"
```

### 3. Generate Your First Image

```bash
python quick_generate.py "./your_reference.jpg" "Barnaby Bunny reading a book in the barn"
```

---

## 📁 Files Included

| File | Purpose |
|------|---------|
| `quick_generate.py` | Simplest option - one image at a time |
| `optimist_farm_generator.py` | Full-featured generator with advanced options |
| `generate_book.py` | Generate entire books from config |
| `optimist_farm_config.json` | Define characters, locations, and book scenes |

---

## 💡 Usage Examples

### Single Image

```python
from quick_generate import generate

generate(
    reference_image="./farm_friends.jpg",
    scene_description="The three friends having a birthday party in the barn"
)
```

### Multiple Scenes

```python
from quick_generate import batch_generate

scenes = [
    "Waking up at sunrise in the hay loft",
    "Eating breakfast together at a wooden table",
    "Discovering a mysterious treasure map",
    "Walking through a flower meadow",
    "Finding the treasure under an oak tree",
    "Celebrating together at sunset"
]

batch_generate(
    reference_image="./farm_friends.jpg",
    scenes=scenes,
    character_desc="Barnaby Bunny in blue overalls, Greta Goat, and Clara Cow"
)
```

### Generate Entire Book

```bash
# List available books
python generate_book.py --list

# Generate a specific book
python generate_book.py book_01_treasure_map ./my_reference.jpg
```

---

## 🎨 Tips for Best Results

### Reference Images
- Use images with **clear character details**
- Include all characters you want in scenes
- **1024x1024 or larger** works best
- Clean backgrounds help (but not required)

### Prompts
- **Be specific**: "sunny morning" vs just "morning"
- **Include emotions**: "excited expression", "looking curious"
- **Describe composition**: "wide shot", "close-up", "from behind"
- **Mention lighting**: "golden hour", "soft diffused light"

### Character Descriptions
Keep these consistent across all generations:
```
Barnaby Bunny: Gray and white bunny, blue denim overalls, plaid shirt, large dark eyes
Greta Goat: Tan goat, spiral horns, white beard, playful expression
Clara Cow: Black and white spotted Holstein calf, pink nose, cheerful
```

---

## 💰 Cost Estimate

| Project Size | Images | Estimated Cost |
|--------------|--------|----------------|
| Single Book (8 pages) | 8 | $0.32 |
| Book + Covers | 10 | $0.40 |
| 12-Book Series | 96 | $3.84 |
| 12 Books + Extras | 150 | $6.00 |

---

## 🔧 Configuration (optimist_farm_config.json)

Define your characters:
```json
{
  "characters": {
    "barnaby_bunny": {
      "name": "Barnaby Bunny",
      "description": "Gray and white bunny wearing blue denim overalls...",
      "reference_image": "./characters/barnaby.jpg"
    }
  }
}
```

Define book scenes:
```json
{
  "books": {
    "book_01_treasure_map": {
      "title": "The Treasure Map Adventure",
      "main_characters": ["barnaby_bunny", "greta_goat", "clara_cow"],
      "scenes": [
        {"page": 1, "prompt": "Waking up at sunrise in the barn"},
        {"page": 2, "prompt": "Discovering a mysterious map"}
      ]
    }
  }
}
```

---

## 🆚 Comparison: This Script vs Leonardo.ai

| Feature | This Script | Leonardo.ai |
|---------|-------------|-------------|
| **Setup** | 5 min CLI | Instant web UI |
| **Interface** | Command line | Drag & drop |
| **Cost** | $0.04/image | $0.01-0.03/image (tokens) |
| **Automation** | Full batch scripts | Manual each image |
| **Consistency** | Excellent (Flux Kontext) | Good (Character Reference) |
| **Best For** | Batch production | Interactive design |

**Recommendation**: Use **Leonardo.ai** ($12-30/mo) for initial character design and experimentation. Use **this script** for batch-generating all your book scenes.

---

## 🤝 Workflow Suggestion

1. **Design characters** in Midjourney or Leonardo.ai
2. **Create reference images** with all characters together
3. **Write scene prompts** for each book page
4. **Batch generate** with this script
5. **Touch up** any imperfect images individually

---

## 🐛 Troubleshooting

**"FAL_KEY not set"**
```bash
export FAL_KEY="your-key-here"
```

**"Module not found"**
```bash
pip install fal-client requests --break-system-packages
```

**"File not found"**
- Check your image path is correct
- Use absolute paths if needed: `/Users/you/images/reference.jpg`

**Images not consistent**
- Use a clearer reference image
- Add more detail to character descriptions
- Try increasing `guidance_scale` to 4.0 or 4.5

---

## 📚 Next Steps

1. Organize your character reference images in `./characters/`
2. Edit `optimist_farm_config.json` with your actual book scenes
3. Generate test images to verify consistency
4. Batch generate all books

Happy illustrating! 🎨
