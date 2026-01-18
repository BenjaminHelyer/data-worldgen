"""
World builder module for generating population data.

This module provides functionality for creating characters and populations
based on probabilistic configurations.
"""

from .population.config import load_config, PopulationConfig
from .population.character_id import generate_character_id
from .population.character import create_character, Character
from . import population_dashboard

__all__ = [
    "load_config",
    "PopulationConfig",
    "generate_character_id",
    "create_character",
    "Character",
    "population_dashboard",
]
