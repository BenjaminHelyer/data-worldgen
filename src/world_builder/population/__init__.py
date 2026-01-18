"""
Population domain module for character generation.

This module contains population-specific functionality including character
generation, population configuration, character IDs, and net worth calculations.
"""

from .config import PopulationConfig, load_config
from .character import Character, create_character
from .character_id import generate_character_id, generate_uuidv7

__all__ = [
    "PopulationConfig",
    "load_config",
    "Character",
    "create_character",
    "generate_character_id",
    "generate_uuidv7",
]
