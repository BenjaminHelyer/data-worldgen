"""
Module for loading the net worth configuration.
This module implements a basic helper function, load_config, to load the net worth configuration.
This helper function returns a Pydantic model, which automatically validates the config.

The config is a JSON file that contains the following fields:
- profession_net_worth: a dictionary mapping professions to their net worth distributions
- metadata: optional metadata fields
"""

from typing import Dict
import json
from pathlib import Path
import math

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self

from world_builder.distributions_config import (
    Distribution,
    NormalDist,
    LogNormalDist,
    TruncatedNormalDist,
)


class NetWorthConfig(BaseModel):
    """
    Loads the net worth config for the world into a Pydantic model.
    """

    model_config = ConfigDict(frozen=True)

    # Maps each profession to its net worth distribution
    profession_net_worth: Dict[str, Distribution] = Field(
        description="Required mapping of professions to their net worth distributions."
    )

    # catch-all dict for any miscellaneous, constant metadata fields
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Optional metadata fields. Can be used to store any string-like constants or metadata.",
    )

    @model_validator(mode="after")
    def validate_distributions(self) -> Self:
        """
        Validates that all distributions are valid.
        """
        for profession, dist in self.profession_net_worth.items():
            if not isinstance(dist, Distribution):
                raise ValueError(
                    f"Invalid distribution for profession '{profession}': {dist}"
                )

            # Validate distribution-specific parameters
            if isinstance(dist, (NormalDist, LogNormalDist)):
                if dist.std <= 0:
                    raise ValueError(
                        f"Standard deviation must be positive for profession '{profession}'. Got {dist.std}"
                    )
                if math.isnan(dist.std) or math.isinf(dist.std):
                    raise ValueError(
                        f"Standard deviation must be finite for profession '{profession}'. Got {dist.std}"
                    )
            elif isinstance(dist, TruncatedNormalDist):
                if dist.std <= 0:
                    raise ValueError(
                        f"Standard deviation must be positive for profession '{profession}'. Got {dist.std}"
                    )
                if math.isnan(dist.std) or math.isinf(dist.std):
                    raise ValueError(
                        f"Standard deviation must be finite for profession '{profession}'. Got {dist.std}"
                    )
                if dist.lower >= dist.upper:
                    raise ValueError(
                        f"Lower bound must be less than upper bound for profession '{profession}'. "
                        f"Got lower={dist.lower}, upper={dist.upper}"
                    )
        return self


def load_config(config_filepath: Path) -> NetWorthConfig:
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
    net_worth_config = NetWorthConfig(**config_json)
    return net_worth_config
