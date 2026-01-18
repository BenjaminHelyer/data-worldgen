"""
Module for loading the net worth configuration.
This module implements a basic helper function, load_config, to load the net worth configuration.
This helper function returns a Pydantic model, which automatically validates the config.

The config is a JSON file that contains the following fields:
- profession_liquid_currency: a dictionary mapping professions to their net worth distributions (required)
- profession_has: an optional dictionary mapping asset types to profession ownership probabilities
- profession_value: an optional dictionary mapping asset types to profession value distributions
- metadata: optional metadata fields
"""

from typing import Dict, Optional
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from world_builder.distributions_config import (
    FunctionBasedDist,
    BernoulliBasedDist,
)


class NetWorthConfig(BaseModel):
    """
    Configuration for net worth generation.

    Attributes:
        profession_liquid_currency: Maps each profession to its net worth distribution (required)
        profession_has: Optional mapping of asset types to profession ownership probabilities
        profession_value: Optional mapping of asset types to profession value distributions
        metadata: Optional metadata fields
    """

    model_config = ConfigDict(frozen=True)

    # required mapping of professions to their net worth distributions
    profession_liquid_currency: Dict[str, FunctionBasedDist] = Field(
        description="Required mapping of professions to their net worth distributions."
    )

    # optional mapping of asset types to profession ownership probabilities
    profession_has: Optional[Dict[str, Dict[str, BernoulliBasedDist]]] = Field(
        default=None,
        description="Optional mapping of asset types to profession ownership probabilities.",
    )

    # optional mapping of asset types to profession value distributions
    profession_value: Optional[Dict[str, Dict[str, FunctionBasedDist]]] = Field(
        default=None,
        description="Optional mapping of asset types to profession value distributions.",
    )

    # catch-all dict for any miscellaneous, constant metadata fields
    metadata: Dict[str, str] = Field(
        default_factory=dict, description="Optional metadata fields."
    )


def load_config(config_path: Path) -> NetWorthConfig:
    """
    Load the net worth configuration from a JSON file.

    Args:
        config_path: Path to the JSON configuration file

    Returns:
        A NetWorthConfig object containing the loaded configuration

    Raises:
        FileNotFoundError: If the config file doesn't exist
        json.JSONDecodeError: If the config file isn't valid JSON
        ValidationError: If the config doesn't match the expected schema
    """
    with open(config_path, encoding="utf-8") as f:
        config_data = json.load(f)
    return NetWorthConfig(**config_data)
