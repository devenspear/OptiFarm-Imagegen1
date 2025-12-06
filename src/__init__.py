"""
Optimist Farm Image Generator
=============================
AI-powered children's storybook illustration generator.

Based on Writing Bible v2.4 and Strategic Playbook 2.0.
"""

from .config_manager import ConfigManager, get_config, reload_config
from .generator import OptimistFarmGenerator, get_generator, GenerationResult

__version__ = "2.0.0"
__all__ = [
    "ConfigManager",
    "get_config",
    "reload_config",
    "OptimistFarmGenerator",
    "get_generator",
    "GenerationResult",
]
