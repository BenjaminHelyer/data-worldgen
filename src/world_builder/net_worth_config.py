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

from pydantic import BaseModel, ConfigDict, Field

from world_builder.distributions_config import Distribution, FunctionBasedDist


class NetWorthConfig(BaseModel):
    """
    Configuration for net worth generation.

    Attributes:
        profession_net_worth: Maps each profession to its net worth distribution
        metadata: Optional metadata fields
    """

    model_config = ConfigDict(frozen=True)

    # Maps each profession to its net worth distribution
    profession_net_worth: Dict[str, FunctionBasedDist] = Field(
        description="Required mapping of professions to their net worth distributions."
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
    with open(config_path) as f:
        config_data = json.load(f)
    return NetWorthConfig(**config_data)
