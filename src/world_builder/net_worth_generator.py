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

    Attributes:
        chain_code: The unique identifier for this net worth record
        liquid_currency: The amount of liquid currency the character has
        currency_type: The type of currency (e.g., "credits", "imperial_credits")
        owns_primary_residence: Whether the character owns their primary residence
        primary_residence_value: The value of the primary residence if owned, None otherwise
        owns_other_properties: Whether the character owns other properties
        other_properties_net_value: The value of other properties if owned, None otherwise
        owns_starships: Whether the character owns starships
        starships_net_value: The value of starships if owned, None otherwise
        owns_speeders: Whether the character owns speeders
        speeders_net_value: The value of speeders if owned, None otherwise
        owns_other_vehicles: Whether the character owns other vehicles
        other_vehicles_net_value: The value of other vehicles if owned, None otherwise
        owns_luxury_property: Whether the character owns luxury property
        luxury_property_net_value: The value of luxury property if owned, None otherwise
        owns_galactic_stock: Whether the character owns galactic stock
        galactic_stock_net_value: The value of galactic stock if owned, None otherwise
        owns_business: Whether the character owns a business
        business_net_value: The value of the business if owned, None otherwise
    """

    def __init__(
        self,
        chain_code: str,
        liquid_currency: float,
        currency_type: str,
        owns_primary_residence: Optional[bool] = None,
        primary_residence_value: Optional[float] = None,
        owns_other_properties: Optional[bool] = None,
        other_properties_net_value: Optional[float] = None,
        owns_starships: Optional[bool] = None,
        starships_net_value: Optional[float] = None,
        owns_speeders: Optional[bool] = None,
        speeders_net_value: Optional[float] = None,
        owns_other_vehicles: Optional[bool] = None,
        other_vehicles_net_value: Optional[float] = None,
        owns_luxury_property: Optional[bool] = None,
        luxury_property_net_value: Optional[float] = None,
        owns_galactic_stock: Optional[bool] = None,
        galactic_stock_net_value: Optional[float] = None,
        owns_business: Optional[bool] = None,
        business_net_value: Optional[float] = None,
    ):
        self._chain_code = chain_code
        self._liquid_currency = liquid_currency
        self._currency_type = currency_type
        self._owns_primary_residence = owns_primary_residence
        self._primary_residence_value = primary_residence_value
        self._owns_other_properties = owns_other_properties
        self._other_properties_net_value = other_properties_net_value
        self._owns_starships = owns_starships
        self._starships_net_value = starships_net_value
        self._owns_speeders = owns_speeders
        self._speeders_net_value = speeders_net_value
        self._owns_other_vehicles = owns_other_vehicles
        self._other_vehicles_net_value = other_vehicles_net_value
        self._owns_luxury_property = owns_luxury_property
        self._luxury_property_net_value = luxury_property_net_value
        self._owns_galactic_stock = owns_galactic_stock
        self._galactic_stock_net_value = galactic_stock_net_value
        self._owns_business = owns_business
        self._business_net_value = business_net_value

    @property
    def chain_code(self) -> str:
        return self._chain_code

    @property
    def liquid_currency(self) -> float:
        return self._liquid_currency

    @property
    def currency_type(self) -> str:
        return self._currency_type

    @property
    def owns_primary_residence(self) -> Optional[bool]:
        return self._owns_primary_residence

    @property
    def primary_residence_value(self) -> Optional[float]:
        return self._primary_residence_value

    @property
    def owns_other_properties(self) -> Optional[bool]:
        return self._owns_other_properties

    @property
    def other_properties_net_value(self) -> Optional[float]:
        return self._other_properties_net_value

    @property
    def owns_starships(self) -> Optional[bool]:
        return self._owns_starships

    @property
    def starships_net_value(self) -> Optional[float]:
        return self._starships_net_value

    @property
    def owns_speeders(self) -> Optional[bool]:
        return self._owns_speeders

    @property
    def speeders_net_value(self) -> Optional[float]:
        return self._speeders_net_value

    @property
    def owns_other_vehicles(self) -> Optional[bool]:
        return self._owns_other_vehicles

    @property
    def other_vehicles_net_value(self) -> Optional[float]:
        return self._other_vehicles_net_value

    @property
    def owns_luxury_property(self) -> Optional[bool]:
        return self._owns_luxury_property

    @property
    def luxury_property_net_value(self) -> Optional[float]:
        return self._luxury_property_net_value

    @property
    def owns_galactic_stock(self) -> Optional[bool]:
        return self._owns_galactic_stock

    @property
    def galactic_stock_net_value(self) -> Optional[float]:
        return self._galactic_stock_net_value

    @property
    def owns_business(self) -> Optional[bool]:
        return self._owns_business

    @property
    def business_net_value(self) -> Optional[float]:
        return self._business_net_value

    def __repr__(self) -> str:
        base_repr = f"NetWorth(chain_code={self.chain_code!r}, liquid_currency={self.liquid_currency}, currency_type={self.currency_type!r}"
        if self.owns_primary_residence is not None:
            base_repr += f", owns_primary_residence={self.owns_primary_residence!r}"
        if self.primary_residence_value is not None:
            base_repr += f", primary_residence_value={self.primary_residence_value!r}"
        if self.owns_other_properties is not None:
            base_repr += f", owns_other_properties={self.owns_other_properties!r}"
        if self.other_properties_net_value is not None:
            base_repr += (
                f", other_properties_net_value={self.other_properties_net_value!r}"
            )
        if self.owns_starships is not None:
            base_repr += f", owns_starships={self.owns_starships!r}"
        if self.starships_net_value is not None:
            base_repr += f", starships_net_value={self.starships_net_value!r}"
        if self.owns_speeders is not None:
            base_repr += f", owns_speeders={self.owns_speeders!r}"
        if self.speeders_net_value is not None:
            base_repr += f", speeders_net_value={self.speeders_net_value!r}"
        if self.owns_other_vehicles is not None:
            base_repr += f", owns_other_vehicles={self.owns_other_vehicles!r}"
        if self.other_vehicles_net_value is not None:
            base_repr += f", other_vehicles_net_value={self.other_vehicles_net_value!r}"
        if self.owns_luxury_property is not None:
            base_repr += f", owns_luxury_property={self.owns_luxury_property!r}"
        if self.luxury_property_net_value is not None:
            base_repr += (
                f", luxury_property_net_value={self.luxury_property_net_value!r}"
            )
        if self.owns_galactic_stock is not None:
            base_repr += f", owns_galactic_stock={self.owns_galactic_stock!r}"
        if self.galactic_stock_net_value is not None:
            base_repr += f", galactic_stock_net_value={self.galactic_stock_net_value!r}"
        if self.owns_business is not None:
            base_repr += f", owns_business={self.owns_business!r}"
        if self.business_net_value is not None:
            base_repr += f", business_net_value={self.business_net_value!r}"
        return base_repr + ")"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NetWorth):
            return NotImplemented
        return (
            self.chain_code == other.chain_code
            and self.liquid_currency == other.liquid_currency
            and self.currency_type == other.currency_type
            and self.owns_primary_residence == other.owns_primary_residence
            and self.primary_residence_value == other.primary_residence_value
            and self.owns_other_properties == other.owns_other_properties
            and self.other_properties_net_value == other.other_properties_net_value
            and self.owns_starships == other.owns_starships
            and self.starships_net_value == other.starships_net_value
            and self.owns_speeders == other.owns_speeders
            and self.speeders_net_value == other.speeders_net_value
            and self.owns_other_vehicles == other.owns_other_vehicles
            and self.other_vehicles_net_value == other.other_vehicles_net_value
            and self.owns_luxury_property == other.owns_luxury_property
            and self.luxury_property_net_value == other.luxury_property_net_value
            and self.owns_galactic_stock == other.owns_galactic_stock
            and self.galactic_stock_net_value == other.galactic_stock_net_value
            and self.owns_business == other.owns_business
            and self.business_net_value == other.business_net_value
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
