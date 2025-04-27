"""
Module for loading the population configuration.
This module implements a basic helper function, load_config, to load the population configuration.
This helper function returns a Pydantic model, which automatically validates the config.

The config is a JSON file that contains the following fields:
- planet: the name of the planet
- city_weights: a dictionary of city names and their weights
- species_weights: a dictionary of species names and their weights
- profession_weights: a dictionary of profession names and their weights
- allegiance_weights: a dictionary of allegiance names and their weights
"""

from typing import Dict
from typing_extensions import Self
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PopulationConfig(BaseModel):
    """
    Loads the population config for the world into a Pydantic model.
    """

    model_config = ConfigDict(frozen=True)

    planet: str = Field(description="The planet name.")
    city_base_probability: Dict[str, float] = Field(
        description="The base probability for each city."
    )
    species_base_probability: Dict[str, float] = Field(
        description="The base probability for each species."
    )
    profession_base_probability: Dict[str, float] = Field(
        description="The base probability for each profession."
    )
    allegiance_base_probability: Dict[str, float] = Field(
        description="The base probability for each allegiance."
    )
    gender_base_probability: Dict[str, float] = Field(
        description="The base probability for each gender."
    )

    @model_validator(mode="after")
    def validate_base_probabilities(self) -> Self:
        """
        Validates the base probabilities for each category.
        Each base probability must sum to unity, otherwise an error will be raised.
        """
        for category in [
            "city_base_probability",
            "species_base_probability",
            "profession_base_probability",
            "allegiance_base_probability",
            "gender_base_probability",
        ]:
            weights = getattr(self, category)
            total_weight = sum(weights.values())
            if abs(total_weight - 1.0) > 1e-6: # add a small tolerance for floating point errors
                raise ValueError(f"Total weight for {category} must be 1.0.")

        # per pydantic convention, return self after validation
        return self


def load_config(config_filepath: Path):
    """
    Loads the JSON configuration file and validates each distribution.
    """
    with open(config_filepath, "r") as f:
        config_json = json.load(f)
    population_config = PopulationConfig(**config_json)
    return population_config
