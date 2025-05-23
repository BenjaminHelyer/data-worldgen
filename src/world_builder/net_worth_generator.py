"""
Module for generating net worth values for characters based on their professions.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import random
import math

from world_builder.net_worth_config import NetWorthConfig
from world_builder.distributions_config import (
    FunctionConfig,
    FunctionBasedDist,
    sample_from_config,
)
from world_builder.character import Character


class NetWorth:
    """
    Represents a character's net worth.

    This class uses dynamic attribute assignment to store net worth information.
    Required attributes:
        - chain_code: The unique identifier for this net worth record
        - liquid_currency: The amount of liquid currency the character has
        - currency_type: The type of currency (e.g., "credits", "imperial_credits")

    Optional attributes are dynamically generated based on asset types:
        For each asset type (e.g. "primary_residence", "starships", etc.):
        - owns_{asset_type}: Whether the character owns this type of asset
        - {asset_type}_value: The value of the asset if owned (or {asset_type}_net_value for some types)
    """

    def __init__(
        self,
        chain_code: str,
        liquid_currency: float,
        currency_type: str,
        **attributes: Any,
    ):
        """
        Initialize a NetWorth instance with required and optional attributes.

        Args:
            chain_code: The unique identifier for this net worth record
            liquid_currency: The amount of liquid currency
            currency_type: The type of currency
            **attributes: Additional attributes to set (e.g. owns_primary_residence, primary_residence_value)
        """
        # Initialize flags and tracking
        super().__setattr__("_initializing", True)
        super().__setattr__("_attribute_names", set())

        # Set required attributes
        self._set_initial_attr("chain_code", chain_code)
        self._set_initial_attr("liquid_currency", liquid_currency)
        self._set_initial_attr("currency_type", currency_type)

        # Set optional attributes dynamically
        for name, value in attributes.items():
            if not name.startswith("_"):  # Only set non-private attributes
                self._set_initial_attr(name, value)

        # Mark initialization as complete
        super().__setattr__("_initializing", False)

    def _set_initial_attr(self, name: str, value: Any) -> None:
        """Helper method for setting initial attributes during initialization."""
        private_name = f"_{name}"
        super().__setattr__(private_name, value)
        self._attribute_names.add(name)
        self._attribute_names.add(private_name)

    def __getattr__(self, name: str) -> Any:
        """
        Provides access to attributes via properties.
        This is called when an attribute is not found through normal lookup.
        """
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        private_name = f"_{name}"
        if hasattr(self, private_name):
            return getattr(self, private_name)

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Prevents modification of attributes after initialization.
        """
        # Allow setting internal flags during initialization
        if name in ("_attribute_names", "_initializing"):
            super().__setattr__(name, value)
            return

        # If we're still initializing, allow setting through the proper method
        if hasattr(self, "_initializing") and self._initializing:
            # This should only happen through _set_initial_attr, but just in case
            super().__setattr__(name, value)
            return

        # After initialization, prevent all attribute modifications
        raise AttributeError(
            f"Can't set attribute '{name}' - NetWorth objects are immutable after initialization"
        )

    def __repr__(self) -> str:
        """
        Returns a string representation of the NetWorth instance.
        """
        attrs = []
        for name in sorted(self._attribute_names):
            if not name.startswith("_"):  # Only include public names in repr
                value = getattr(self, name)
                attrs.append(f"{name}={value!r}")
        return f"NetWorth({', '.join(attrs)})"

    def __eq__(self, other: object) -> bool:
        """
        Compares two NetWorth instances for equality.
        """
        if not isinstance(other, NetWorth):
            return NotImplemented
        return all(
            getattr(self, name) == getattr(other, name)
            for name in self._attribute_names
            if not name.startswith("_")
        )


def evaluate_function(func_config: FunctionConfig, x: float) -> float:
    """
    Evaluate a function configuration at a given x value.

    Args:
        func_config: The function configuration to evaluate
        x: The input value

    Returns:
        The function value at x
    """
    if func_config.type == "constant":
        return func_config.params.value
    elif func_config.type == "linear":
        return func_config.params.slope * x + func_config.params.intercept
    elif func_config.type == "exponential":
        return func_config.params.base * math.exp(func_config.params.rate * x)
    elif func_config.type == "quadratic":
        return (
            func_config.params.a * x * x
            + func_config.params.b * x
            + func_config.params.c
        )
    else:
        raise ValueError(f"Unknown function type: {func_config.type}")


def _generate_asset_value(
    character: Character,
    has_config: Optional[Dict[str, Any]],
    value_config: Optional[Dict[str, Any]],
    profession: str,
    asset_type: str,
) -> tuple[Optional[bool], Optional[float]]:
    """
    Helper function to generate ownership and value for an asset type.

    Args:
        character: The character to generate for
        has_config: The configuration for asset ownership probability
        value_config: The configuration for asset value distribution
        profession: The character's profession
        asset_type: The type of asset to generate for

    Returns:
        A tuple of (owns_asset, asset_value) where both could be None
    """
    owns_asset = None
    asset_value = None

    if (
        has_config is not None
        and asset_type in has_config
        and profession in has_config[asset_type]
    ):
        residence_config = has_config[asset_type][profession]
        field_value = getattr(character, residence_config.field_name)
        probability = evaluate_function(residence_config.mean_function, field_value)
        # Ensure probability is between 0 and 1
        probability = max(0.0, min(1.0, probability))
        owns_asset = random.random() < probability

        # If they own the asset, generate its value
        if owns_asset and value_config is not None:
            if asset_type in value_config and profession in value_config[asset_type]:
                value_config_data = value_config[asset_type][profession]
                field_value = getattr(character, value_config_data.field_name)
                config_dict = value_config_data.model_dump()
                config_dict["type"] = "function_based"
                asset_value = sample_from_config(config_dict, field_value)
                # Ensure the value is positive
                asset_value = max(0, asset_value)

    return owns_asset, asset_value


def generate_net_worth(character: Character, config: NetWorthConfig) -> NetWorth:
    """
    Generate a net worth value for a character based on their profession.

    Args:
        character: The character to generate net worth for
        config: The net worth configuration containing profession-based functions

    Returns:
        A NetWorth object with the generated values

    Raises:
        ValueError: If the character's profession is not found in the config
    """
    if character.profession not in config.profession_liquid_currency:
        raise ValueError(
            f"Character profession '{character.profession}' not found in net worth config"
        )

    # Get the configuration for this profession
    prof_config = config.profession_liquid_currency[character.profession]

    # Get the field value (e.g., age) from the character
    field_value = getattr(character, prof_config.field_name)

    # Generate the net worth using the distribution
    config_dict = prof_config.model_dump()
    config_dict["type"] = "function_based"  # Add the type field
    liquid_currency = sample_from_config(config_dict, field_value)

    # Ensure the value is positive
    liquid_currency = max(0, liquid_currency)

    # Get currency type from metadata, defaulting to "credits" if not specified
    currency_type = config.metadata.get("currency", "credits")

    # Generate all asset ownership and values
    owns_primary_residence, primary_residence_value = _generate_asset_value(
        character,
        config.profession_has,
        config.profession_value,
        character.profession,
        "primary_residence",
    )

    owns_other_properties, other_properties_net_value = _generate_asset_value(
        character,
        config.profession_has,
        config.profession_value,
        character.profession,
        "other_properties",
    )

    owns_starships, starships_net_value = _generate_asset_value(
        character,
        config.profession_has,
        config.profession_value,
        character.profession,
        "starships",
    )

    owns_speeders, speeders_net_value = _generate_asset_value(
        character,
        config.profession_has,
        config.profession_value,
        character.profession,
        "speeders",
    )

    owns_other_vehicles, other_vehicles_net_value = _generate_asset_value(
        character,
        config.profession_has,
        config.profession_value,
        character.profession,
        "other_vehicles",
    )

    owns_luxury_property, luxury_property_net_value = _generate_asset_value(
        character,
        config.profession_has,
        config.profession_value,
        character.profession,
        "luxury_property",
    )

    owns_galactic_stock, galactic_stock_net_value = _generate_asset_value(
        character,
        config.profession_has,
        config.profession_value,
        character.profession,
        "galactic_stock",
    )

    owns_business, business_net_value = _generate_asset_value(
        character,
        config.profession_has,
        config.profession_value,
        character.profession,
        "business",
    )

    return NetWorth(
        chain_code=character.chain_code,
        liquid_currency=liquid_currency,
        currency_type=currency_type,
        owns_primary_residence=owns_primary_residence,
        primary_residence_value=primary_residence_value,
        owns_other_properties=owns_other_properties,
        other_properties_net_value=other_properties_net_value,
        owns_starships=owns_starships,
        starships_net_value=starships_net_value,
        owns_speeders=owns_speeders,
        speeders_net_value=speeders_net_value,
        owns_other_vehicles=owns_other_vehicles,
        other_vehicles_net_value=other_vehicles_net_value,
        owns_luxury_property=owns_luxury_property,
        luxury_property_net_value=luxury_property_net_value,
        owns_galactic_stock=owns_galactic_stock,
        galactic_stock_net_value=galactic_stock_net_value,
        owns_business=owns_business,
        business_net_value=business_net_value,
    )
