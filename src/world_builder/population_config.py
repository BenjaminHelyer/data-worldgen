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

from world_builder.distributions_config import Distribution


class PopulationConfig(BaseModel):
    """
    Loads the population config for the world into a Pydantic model.

    This model is strict on the base probabilities for each category.
    This is because we expect there will be a minimum amount of categories that will
    be useful for our world generation example, i.e., this is a strict contract on the
    data that could be generated.

    The model is more flexible on the model factors.
    """

    model_config = ConfigDict(frozen=True)

    # finite base probabilities allow the user to specify the probability for fields where one of several values may be chosen
    # so, for example, nested in the "base_probabilities_discrete" key in the config, we might have:
    #   {"base_probabilities_discrete":
    #       "city": {
    #           "Mos Eisley": 0.5,
    #           "Mos Espa": 0.5 } ...}
    base_probabilities_finite: Dict[str, Dict[str, float]] = Field(
        description="Required base probabilities for discrete fields. All probabilities within a specific base probability must sum to unity."
    )

    # distribution base probabilities allow the user to draw a field from some distribution with a specified parameter list
    # for example, they could specify 'age' to be drawn from a normal distribution with mean=30 and std=15
    base_probabilities_distributions: Dict[str, Distribution]

    # this is probably the most gnarly part of the config
    # we use a factor-graph approach which means we need a nested dict of factors
    # an example is probably useful here...the expected JSON is of the form:
    # {..."factors": {
    #           "city": {
    #               "allegiance": {
    #                   "Mos Eisley": {
    #                       "Imperial": 5.0 ...}
    # the above JSON would multiply the chances of a character in Mos Eisley being an Imperial by a factor of 5
    # i.e., it's a statement of the form, "If a character is in Mos Eisley, then they are 5x more likely to be an Imperial"
    factors: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = Field(
        default_factory=dict,
        description=(
            "Optional nested factors: factor_name -> dimension_name -> key -> subkey -> multiplier."
            "All multipliers must be non-negative."
        ),
    )

    @model_validator(mode="after")
    def validate_base_probabilities(self) -> Self:
        """
        Validates the base probabilities for each category.
        Each base probability must sum to unity, otherwise an error will be raised.
        """
        for category in self.base_probabilities_finite.keys():
            total_weight = sum(
                [prob for prob in self.base_probabilities_finite[category].values()]
            )
            if (
                abs(total_weight - 1.0) > 1e-6
            ):  # add a small tolerance for floating point errors
                raise ValueError(
                    f"Base probabilities for {category} must be 1.0. Received {total_weight} != 1.0"
                )

        # per pydantic convention, return self after validation
        return self

    @model_validator(mode="after")
    def validate_factors(self) -> Self:
        """
        Validates nested factor multipliers are structured and non-negative.
        """
        for factor_name, dims in self.factors.items():
            if not isinstance(dims, dict):
                raise ValueError(
                    f"Factor '{factor_name}' must map to a dict of dimensions."
                )
            for dimension, mapping in dims.items():
                if not isinstance(mapping, dict):
                    raise ValueError(
                        f"Factor '{factor_name}' dimension '{dimension}' must be a dict of key→subkey mappings."
                    )
                for key, submap in mapping.items():
                    if not isinstance(submap, dict):
                        raise ValueError(
                            f"Factor '{factor_name}'[{dimension}]['{key}'] must be a dict of subkey→multiplier."
                        )
                    for subkey, multiplier in submap.items():
                        if not isinstance(multiplier, (int, float)) or multiplier < 0:
                            raise ValueError(
                                f"Multiplier for factor '{factor_name}'[{dimension}]['{key}']['{subkey}'] "
                                f"must be non-negative number (got {multiplier})."
                            )
        return self


def load_config(config_filepath: Path) -> PopulationConfig:
    """
    Loads the JSON configuration file and validates each distribution.
    """
    with open(config_filepath, "r") as f:
        try:
            config_json = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Tried to load {config_filepath} into JSON object and failed. Check to ensure it the file provided is valid JSON."
            ) from e
    population_config = PopulationConfig(**config_json)
    return population_config
