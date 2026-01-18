"""
World builder module for generating population and ecosystem data.

This module provides functionality for creating characters and populations,
as well as animals and ecosystems, based on probabilistic configurations.
"""

from .population.config import load_config, PopulationConfig
from .population.character_id import generate_character_id
from .population.character import create_character, Character
from . import population_dashboard

# Ecosystem module exports
from .ecosystem.config import load_config as load_ecosystem_config, EcosystemConfig
from .ecosystem.animal_id import generate_animal_id
from .ecosystem.animal import create_animal, Animal

__all__ = [
    # Population exports
    "load_config",
    "PopulationConfig",
    "generate_character_id",
    "create_character",
    "Character",
    "population_dashboard",
    # Ecosystem exports
    "load_ecosystem_config",
    "EcosystemConfig",
    "generate_animal_id",
    "create_animal",
    "Animal",
]
