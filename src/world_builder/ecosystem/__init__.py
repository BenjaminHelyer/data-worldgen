"""
Ecosystem domain module for animal generation.

This module contains ecosystem-specific functionality including animal
generation, ecosystem configuration, animal IDs, and dashboard visualization.
"""

from .config import EcosystemConfig, load_config
from .animal import Animal, create_animal
from .animal_id import generate_animal_id, generate_uuidv7
from . import dashboard

__all__ = [
    "EcosystemConfig",
    "load_config",
    "Animal",
    "create_animal",
    "generate_animal_id",
    "generate_uuidv7",
    "dashboard",
]
