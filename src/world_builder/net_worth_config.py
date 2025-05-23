"""
Module for loading the net worth configuration.
This module implements a basic helper function, load_config, to load the net worth configuration.
This helper function returns a Pydantic model, which automatically validates the config.

The config is a JSON file that contains the following fields:
- profession_liquid_currency: a dictionary mapping professions to their net worth distributions
- profession_has_primary_residence: an optional dictionary mapping professions to their probability of owning a residence
- profession_primary_residence_value: an optional dictionary mapping professions to their residence value distribution
- profession_has_other_properties: an optional dictionary mapping professions to their probability of owning other properties
- profession_other_properties_net_value: an optional dictionary mapping professions to their other properties value distribution
- profession_has_starships: an optional dictionary mapping professions to their probability of owning starships
- profession_starships_net_value: an optional dictionary mapping professions to their starships value distribution
- profession_has_speeders: an optional dictionary mapping professions to their probability of owning speeders
- profession_speeders_net_value: an optional dictionary mapping professions to their speeders value distribution
- profession_has_other_vehicles: an optional dictionary mapping professions to their probability of owning other vehicles
- profession_other_vehicles_net_value: an optional dictionary mapping professions to their other vehicles value distribution
- profession_has_luxury_property: an optional dictionary mapping professions to their probability of owning luxury property
- profession_luxury_property_net_value: an optional dictionary mapping professions to their luxury property value distribution
- profession_has_galactic_stock: an optional dictionary mapping professions to their probability of owning galactic stock
- profession_galactic_stock_net_value: an optional dictionary mapping professions to their galactic stock value distribution
- profession_has_business: an optional dictionary mapping professions to their probability of owning a business
- profession_business_net_value: an optional dictionary mapping professions to their business value distribution
- metadata: optional metadata fields
"""

from typing import Dict, Optional
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from world_builder.distributions_config import (
    Distribution,
    FunctionBasedDist,
    FunctionConfig,
    BernoulliBasedDist,
)


class NetWorthConfig(BaseModel):
    """
    Configuration for net worth generation.

    Attributes:
        profession_liquid_currency: Maps each profession to its net worth distribution
        profession_has_primary_residence: Optional mapping of professions to their residence ownership probability
        profession_primary_residence_value: Optional mapping of professions to their residence value distribution
        profession_has_other_properties: Optional mapping of professions to their other properties ownership probability
        profession_other_properties_net_value: Optional mapping of professions to their other properties value distribution
        profession_has_starships: Optional mapping of professions to their starships ownership probability
        profession_starships_net_value: Optional mapping of professions to their starships value distribution
        profession_has_speeders: Optional mapping of professions to their speeders ownership probability
        profession_speeders_net_value: Optional mapping of professions to their speeders value distribution
        profession_has_other_vehicles: Optional mapping of professions to their other vehicles ownership probability
        profession_other_vehicles_net_value: Optional mapping of professions to their other vehicles value distribution
        profession_has_luxury_property: Optional mapping of professions to their luxury property ownership probability
        profession_luxury_property_net_value: Optional mapping of professions to their luxury property value distribution
        profession_has_galactic_stock: Optional mapping of professions to their galactic stock ownership probability
        profession_galactic_stock_net_value: Optional mapping of professions to their galactic stock value distribution
        profession_has_business: Optional mapping of professions to their business ownership probability
        profession_business_net_value: Optional mapping of professions to their business value distribution
        metadata: Optional metadata fields
    """

    model_config = ConfigDict(frozen=True)

    # Maps each profession to its net worth distribution
    profession_liquid_currency: Dict[str, FunctionBasedDist] = Field(
        description="Required mapping of professions to their net worth distributions."
    )

    # Optional mapping of professions to their residence ownership probability
    profession_has_primary_residence: Optional[Dict[str, BernoulliBasedDist]] = Field(
        default=None,
        description="Optional mapping of professions to their residence ownership probability.",
    )

    # Optional mapping of professions to their residence value distribution
    profession_primary_residence_value: Optional[Dict[str, FunctionBasedDist]] = Field(
        default=None,
        description="Optional mapping of professions to their residence value distribution.",
    )

    # Optional mapping of professions to their other properties ownership probability
    profession_has_other_properties: Optional[Dict[str, BernoulliBasedDist]] = Field(
        default=None,
        description="Optional mapping of professions to their other properties ownership probability.",
    )

    # Optional mapping of professions to their other properties value distribution
    profession_other_properties_net_value: Optional[Dict[str, FunctionBasedDist]] = (
        Field(
            default=None,
            description="Optional mapping of professions to their other properties value distribution.",
        )
    )

    # Optional mapping of professions to their starships ownership probability
    profession_has_starships: Optional[Dict[str, BernoulliBasedDist]] = Field(
        default=None,
        description="Optional mapping of professions to their starships ownership probability.",
    )

    # Optional mapping of professions to their starships value distribution
    profession_starships_net_value: Optional[Dict[str, FunctionBasedDist]] = Field(
        default=None,
        description="Optional mapping of professions to their starships value distribution.",
    )

    # Optional mapping of professions to their speeders ownership probability
    profession_has_speeders: Optional[Dict[str, BernoulliBasedDist]] = Field(
        default=None,
        description="Optional mapping of professions to their speeders ownership probability.",
    )

    # Optional mapping of professions to their speeders value distribution
    profession_speeders_net_value: Optional[Dict[str, FunctionBasedDist]] = Field(
        default=None,
        description="Optional mapping of professions to their speeders value distribution.",
    )

    # Optional mapping of professions to their other vehicles ownership probability
    profession_has_other_vehicles: Optional[Dict[str, BernoulliBasedDist]] = Field(
        default=None,
        description="Optional mapping of professions to their other vehicles ownership probability.",
    )

    # Optional mapping of professions to their other vehicles value distribution
    profession_other_vehicles_net_value: Optional[Dict[str, FunctionBasedDist]] = Field(
        default=None,
        description="Optional mapping of professions to their other vehicles value distribution.",
    )

    # Optional mapping of professions to their luxury property ownership probability
    profession_has_luxury_property: Optional[Dict[str, BernoulliBasedDist]] = Field(
        default=None,
        description="Optional mapping of professions to their luxury property ownership probability.",
    )

    # Optional mapping of professions to their luxury property value distribution
    profession_luxury_property_net_value: Optional[Dict[str, FunctionBasedDist]] = (
        Field(
            default=None,
            description="Optional mapping of professions to their luxury property value distribution.",
        )
    )

    # Optional mapping of professions to their galactic stock ownership probability
    profession_has_galactic_stock: Optional[Dict[str, BernoulliBasedDist]] = Field(
        default=None,
        description="Optional mapping of professions to their galactic stock ownership probability.",
    )

    # Optional mapping of professions to their galactic stock value distribution
    profession_galactic_stock_net_value: Optional[Dict[str, FunctionBasedDist]] = Field(
        default=None,
        description="Optional mapping of professions to their galactic stock value distribution.",
    )

    # Optional mapping of professions to their business ownership probability
    profession_has_business: Optional[Dict[str, BernoulliBasedDist]] = Field(
        default=None,
        description="Optional mapping of professions to their business ownership probability.",
    )

    # Optional mapping of professions to their business value distribution
    profession_business_net_value: Optional[Dict[str, FunctionBasedDist]] = Field(
        default=None,
        description="Optional mapping of professions to their business value distribution.",
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
