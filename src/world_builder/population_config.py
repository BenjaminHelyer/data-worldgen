from typing import Dict, Literal, Self
import json

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
