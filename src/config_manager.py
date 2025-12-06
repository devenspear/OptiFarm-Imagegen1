#!/usr/bin/env python3
"""
Configuration Manager for Optimist Farm Image Generator
========================================================
Handles loading, validating, and managing all configuration settings.
Supports hot-reloading and config overrides.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from copy import deepcopy


@dataclass
class ImageSettings:
    """Image generation settings."""
    aspect_ratios: Dict[str, str] = field(default_factory=dict)
    default_aspect_ratio: str = "square"
    hero_shot_ratio: str = "square"
    scene_ratio: str = "landscape"
    cover_ratio: str = "portrait"
    group_shot_ratio: str = "landscape"

    def get_ratio(self, ratio_type: str) -> str:
        """Get aspect ratio for a given type."""
        ratio_map = {
            "hero": self.hero_shot_ratio,
            "scene": self.scene_ratio,
            "cover": self.cover_ratio,
            "group": self.group_shot_ratio,
            "default": self.default_aspect_ratio
        }
        ratio_key = ratio_map.get(ratio_type, self.default_aspect_ratio)
        return self.aspect_ratios.get(ratio_key, "1:1")


@dataclass
class Character:
    """Character definition."""
    id: str
    name: str
    role: str
    description: str
    personality: str
    visual_cues: str
    virtues: List[str]
    reference_image: str
    locations: List[str] = field(default_factory=list)
    special_function: Optional[str] = None
    appears_with_chime: bool = False

    @classmethod
    def from_dict(cls, char_id: str, data: Dict) -> 'Character':
        """Create Character from dictionary."""
        return cls(
            id=char_id,
            name=data.get("name", ""),
            role=data.get("role", "core"),
            description=data.get("description", ""),
            personality=data.get("personality", ""),
            visual_cues=data.get("visual_cues", ""),
            virtues=data.get("virtues", []),
            reference_image=data.get("reference_image", ""),
            locations=data.get("locations", []),
            special_function=data.get("special_function"),
            appears_with_chime=data.get("appears_with_chime", False)
        )


@dataclass
class Location:
    """Location definition."""
    id: str
    name: str
    description: str
    associated_virtues: List[str]
    associated_characters: List[str]

    @classmethod
    def from_dict(cls, loc_id: str, data: Dict) -> 'Location':
        """Create Location from dictionary."""
        return cls(
            id=loc_id,
            name=data.get("name", ""),
            description=data.get("description", ""),
            associated_virtues=data.get("associated_virtues", []),
            associated_characters=data.get("associated_characters", [])
        )


@dataclass
class Book:
    """Book definition."""
    id: str
    title: str
    book_number: int
    virtue: str
    featured_character: str
    supporting_characters: List[str]
    primary_location: str
    prop: str
    mantra: str
    micro_ritual: Dict[str, str]
    scenes: List[Dict]

    @classmethod
    def from_dict(cls, book_id: str, data: Dict) -> 'Book':
        """Create Book from dictionary."""
        return cls(
            id=book_id,
            title=data.get("title", ""),
            book_number=data.get("book_number", 0),
            virtue=data.get("virtue", ""),
            featured_character=data.get("featured_character", ""),
            supporting_characters=data.get("supporting_characters", []),
            primary_location=data.get("primary_location", ""),
            prop=data.get("prop", ""),
            mantra=data.get("mantra", ""),
            micro_ritual=data.get("micro_ritual", {}),
            scenes=data.get("scenes", [])
        )


class ConfigManager:
    """
    Manages all configuration for the Optimist Farm generator.

    Features:
    - Loads from master config file
    - Supports config overrides
    - Provides typed access to characters, locations, books
    - Allows runtime modifications
    - Saves modified configs
    """

    DEFAULT_CONFIG_PATH = "./config/master_config.json"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to config file. Uses default if not specified.
        """
        self.config_path = Path(config_path or self.DEFAULT_CONFIG_PATH)
        self._raw_config: Dict = {}
        self._characters: Dict[str, Character] = {}
        self._locations: Dict[str, Location] = {}
        self._books: Dict[str, Book] = {}
        self._style_presets: Dict[str, Dict] = {}
        self._prompt_templates: Dict[str, str] = {}
        self._image_settings: Optional[ImageSettings] = None

        self.load()

    def load(self, config_path: Optional[str] = None) -> None:
        """
        Load configuration from file.

        Args:
            config_path: Optional override path
        """
        path = Path(config_path) if config_path else self.config_path

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r") as f:
            self._raw_config = json.load(f)

        self._parse_config()
        print(f"Loaded config from: {path}")

    def _parse_config(self) -> None:
        """Parse raw config into typed objects."""
        # Parse characters
        self._characters = {}
        for char_id, char_data in self._raw_config.get("characters", {}).items():
            self._characters[char_id] = Character.from_dict(char_id, char_data)

        # Parse locations
        self._locations = {}
        for loc_id, loc_data in self._raw_config.get("locations", {}).items():
            self._locations[loc_id] = Location.from_dict(loc_id, loc_data)

        # Parse books
        self._books = {}
        for book_id, book_data in self._raw_config.get("books", {}).items():
            self._books[book_id] = Book.from_dict(book_id, book_data)

        # Parse style presets
        self._style_presets = self._raw_config.get("style_presets", {})

        # Parse prompt templates
        self._prompt_templates = self._raw_config.get("prompt_templates", {})

        # Parse image settings
        img_settings = self._raw_config.get("image_settings", {})
        self._image_settings = ImageSettings(
            aspect_ratios=img_settings.get("aspect_ratios", {}),
            default_aspect_ratio=img_settings.get("default_aspect_ratio", "square"),
            hero_shot_ratio=img_settings.get("hero_shot_ratio", "square"),
            scene_ratio=img_settings.get("scene_ratio", "landscape"),
            cover_ratio=img_settings.get("cover_ratio", "portrait"),
            group_shot_ratio=img_settings.get("group_shot_ratio", "landscape")
        )

    def save(self, path: Optional[str] = None) -> None:
        """
        Save current configuration to file.

        Args:
            path: Optional output path. Uses original path if not specified.
        """
        output_path = Path(path) if path else self.config_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(self._raw_config, f, indent=2)

        print(f"Saved config to: {output_path}")

    # =========================================================================
    # Property Accessors
    # =========================================================================

    @property
    def project_name(self) -> str:
        """Get project name."""
        return self._raw_config.get("project", {}).get("name", "Optimist Farm")

    @property
    def api_config(self) -> Dict:
        """Get API configuration."""
        return self._raw_config.get("api", {})

    @property
    def api_model(self) -> str:
        """Get API model identifier."""
        return self.api_config.get("model", "fal-ai/flux-pro/kontext")

    @property
    def api_defaults(self) -> Dict:
        """Get API default parameters."""
        return self.api_config.get("defaults", {
            "guidance_scale": 3.5,
            "num_inference_steps": 28,
            "output_format": "jpeg"
        })

    @property
    def cost_per_image(self) -> float:
        """Get cost per image."""
        return self.api_config.get("cost_per_image", 0.04)

    @property
    def paths(self) -> Dict[str, str]:
        """Get configured paths."""
        return self._raw_config.get("paths", {})

    @property
    def image_settings(self) -> ImageSettings:
        """Get image settings."""
        return self._image_settings

    @property
    def active_style(self) -> str:
        """Get active style preset name."""
        return self._raw_config.get("active_style", "default")

    @property
    def active_style_prompt(self) -> str:
        """Get the prompt for the active style."""
        style_data = self._style_presets.get(self.active_style, {})
        return style_data.get("prompt", "")

    @property
    def generation_settings(self) -> Dict:
        """Get generation settings."""
        return self._raw_config.get("generation_settings", {})

    # =========================================================================
    # Character Methods
    # =========================================================================

    @property
    def characters(self) -> Dict[str, Character]:
        """Get all characters."""
        return self._characters

    def get_character(self, char_id: str) -> Optional[Character]:
        """Get a specific character by ID."""
        return self._characters.get(char_id)

    def get_characters_by_role(self, role: str) -> List[Character]:
        """Get all characters with a specific role."""
        return [c for c in self._characters.values() if c.role == role]

    def get_characters_by_virtue(self, virtue: str) -> List[Character]:
        """Get all characters associated with a virtue."""
        return [c for c in self._characters.values() if virtue in c.virtues]

    def list_character_ids(self) -> List[str]:
        """List all character IDs."""
        return list(self._characters.keys())

    def list_characters(self) -> List[Dict[str, str]]:
        """List characters with basic info."""
        return [
            {"id": c.id, "name": c.name, "role": c.role}
            for c in self._characters.values()
        ]

    # =========================================================================
    # Location Methods
    # =========================================================================

    @property
    def locations(self) -> Dict[str, Location]:
        """Get all locations."""
        return self._locations

    def get_location(self, loc_id: str) -> Optional[Location]:
        """Get a specific location by ID."""
        return self._locations.get(loc_id)

    def list_location_ids(self) -> List[str]:
        """List all location IDs."""
        return list(self._locations.keys())

    def list_locations(self) -> List[Dict[str, str]]:
        """List locations with basic info."""
        return [
            {"id": loc.id, "name": loc.name}
            for loc in self._locations.values()
        ]

    # =========================================================================
    # Book Methods
    # =========================================================================

    @property
    def books(self) -> Dict[str, Book]:
        """Get all books."""
        return self._books

    def get_book(self, book_id: str) -> Optional[Book]:
        """Get a specific book by ID."""
        return self._books.get(book_id)

    def list_book_ids(self) -> List[str]:
        """List all book IDs."""
        return list(self._books.keys())

    def list_books(self) -> List[Dict[str, Any]]:
        """List books with basic info."""
        return [
            {
                "id": book.id,
                "number": book.book_number,
                "title": book.title,
                "virtue": book.virtue,
                "featured_character": book.featured_character
            }
            for book in sorted(self._books.values(), key=lambda b: b.book_number)
        ]

    # =========================================================================
    # Style Methods
    # =========================================================================

    @property
    def style_presets(self) -> Dict[str, Dict]:
        """Get all style presets."""
        return self._style_presets

    def get_style_prompt(self, style_name: str) -> str:
        """Get prompt for a specific style."""
        style_data = self._style_presets.get(style_name, {})
        return style_data.get("prompt", "")

    def set_active_style(self, style_name: str) -> bool:
        """Set the active style preset."""
        if style_name in self._style_presets:
            self._raw_config["active_style"] = style_name
            return True
        return False

    def list_styles(self) -> List[Dict[str, str]]:
        """List available styles."""
        return [
            {"id": style_id, "name": style_data.get("name", style_id)}
            for style_id, style_data in self._style_presets.items()
        ]

    # =========================================================================
    # Prompt Template Methods
    # =========================================================================

    @property
    def prompt_templates(self) -> Dict[str, str]:
        """Get all prompt templates."""
        return self._prompt_templates

    def get_prompt_template(self, template_name: str) -> str:
        """Get a specific prompt template."""
        return self._prompt_templates.get(template_name, "")

    def build_prompt(self, template_name: str, **kwargs) -> str:
        """
        Build a prompt from a template with variable substitution.

        Args:
            template_name: Name of the template to use
            **kwargs: Variables to substitute

        Returns:
            Formatted prompt string
        """
        template = self.get_prompt_template(template_name)
        if not template:
            return ""

        # Add style prompt if not provided
        if "style_prompt" not in kwargs:
            kwargs["style_prompt"] = self.active_style_prompt

        # Format with available kwargs, leave missing placeholders
        try:
            return template.format(**kwargs)
        except KeyError as e:
            # Return partial format if some keys missing
            for key, value in kwargs.items():
                template = template.replace(f"{{{key}}}", str(value))
            return template

    # =========================================================================
    # Configuration Modification Methods
    # =========================================================================

    def set_value(self, key_path: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.

        Args:
            key_path: Dot-separated path (e.g., "image_settings.default_aspect_ratio")
            value: Value to set
        """
        keys = key_path.split(".")
        config = self._raw_config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value
        self._parse_config()  # Re-parse to update typed objects

    def get_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key_path: Dot-separated path
            default: Default value if not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split(".")
        config = self._raw_config

        for key in keys:
            if isinstance(config, dict) and key in config:
                config = config[key]
            else:
                return default

        return config

    def add_character(self, char_id: str, char_data: Dict) -> None:
        """Add a new character to configuration."""
        self._raw_config.setdefault("characters", {})[char_id] = char_data
        self._characters[char_id] = Character.from_dict(char_id, char_data)

    def update_character(self, char_id: str, updates: Dict) -> bool:
        """Update an existing character."""
        if char_id not in self._raw_config.get("characters", {}):
            return False

        self._raw_config["characters"][char_id].update(updates)
        self._characters[char_id] = Character.from_dict(
            char_id, self._raw_config["characters"][char_id]
        )
        return True

    def add_style_preset(self, style_id: str, name: str, prompt: str) -> None:
        """Add a new style preset."""
        self._raw_config.setdefault("style_presets", {})[style_id] = {
            "name": name,
            "prompt": prompt
        }
        self._style_presets = self._raw_config["style_presets"]

    def update_book_scenes(self, book_id: str, scenes: List[Dict]) -> bool:
        """Update scenes for a book."""
        if book_id not in self._raw_config.get("books", {}):
            return False

        self._raw_config["books"][book_id]["scenes"] = scenes
        self._books[book_id] = Book.from_dict(
            book_id, self._raw_config["books"][book_id]
        )
        return True

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_character_description_block(self, char_ids: List[str]) -> str:
        """
        Build a description block for multiple characters.

        Args:
            char_ids: List of character IDs

        Returns:
            Formatted description string
        """
        descriptions = []
        for char_id in char_ids:
            char = self.get_character(char_id)
            if char:
                descriptions.append(f"{char.name}: {char.description}")
        return "\n".join(descriptions)

    def get_book_characters(self, book_id: str) -> List[Character]:
        """Get all characters for a book (featured + supporting)."""
        book = self.get_book(book_id)
        if not book:
            return []

        char_ids = [book.featured_character] + book.supporting_characters
        return [self.get_character(cid) for cid in char_ids if self.get_character(cid)]

    def export_config(self) -> Dict:
        """Export full configuration as dictionary."""
        return deepcopy(self._raw_config)

    def print_summary(self) -> None:
        """Print configuration summary."""
        print(f"\n{'='*50}")
        print(f"OPTIMIST FARM CONFIGURATION")
        print(f"{'='*50}")
        print(f"Project: {self.project_name}")
        print(f"Config file: {self.config_path}")
        print(f"\nCharacters: {len(self._characters)}")
        print(f"Locations: {len(self._locations)}")
        print(f"Books: {len(self._books)}")
        print(f"Style presets: {len(self._style_presets)}")
        print(f"Active style: {self.active_style}")
        print(f"\nAPI: {self.api_model}")
        print(f"Cost per image: ${self.cost_per_image}")
        print(f"{'='*50}\n")


# =============================================================================
# Convenience Functions
# =============================================================================

_default_config: Optional[ConfigManager] = None

def get_config(config_path: Optional[str] = None) -> ConfigManager:
    """
    Get the configuration manager (singleton pattern).

    Args:
        config_path: Optional path to load from

    Returns:
        ConfigManager instance
    """
    global _default_config

    if _default_config is None or config_path:
        _default_config = ConfigManager(config_path)

    return _default_config


def reload_config() -> ConfigManager:
    """Reload configuration from disk."""
    global _default_config
    if _default_config:
        _default_config.load()
    return _default_config


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    import sys

    config_path = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        config = ConfigManager(config_path)
        config.print_summary()

        print("Characters:")
        for char in config.list_characters():
            print(f"  - {char['id']}: {char['name']} ({char['role']})")

        print("\nLocations:")
        for loc in config.list_locations():
            print(f"  - {loc['id']}: {loc['name']}")

        print("\nBooks:")
        for book in config.list_books():
            print(f"  - Book {book['number']}: {book['title']} ({book['virtue']})")

        print("\nStyles:")
        for style in config.list_styles():
            print(f"  - {style['id']}: {style['name']}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Run from the project root directory or specify config path.")
