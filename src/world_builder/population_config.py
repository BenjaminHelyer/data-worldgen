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
    city_weights: Dict[str, float] = Field(description="The weights for each city.")
    species_weights: Dict[str, float] = Field(
        description="The weights for each species."
    )
    profession_weights: Dict[str, float] = Field(
        description="The weights for each profession."
    )
    allegiance_weights: Dict[str, float] = Field(
        description="The weights for each allegiance."
    )
    gender_weights: Dict[str, float] = Field(description="The weights for each gender.")

    @model_validator(mode="after")
    def validate_weights(self) -> Self:
        """
        Validates the weights for each category.
        """
        for category in [
            "city_weights",
            "species_weights",
            "profession_weights",
            "allegiance_weights",
        ]:
            weights = getattr(self, category)
            total_weight = sum(weights.values())
            if not total_weight == 1.0:
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
