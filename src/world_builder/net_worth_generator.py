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
    """

    def __init__(
        self,
        chain_code: str,
        liquid_currency: float,
        currency_type: str,
        owns_primary_residence: Optional[bool] = None,
        primary_residence_value: Optional[float] = None,
    ):
        self._chain_code = chain_code
        self._liquid_currency = liquid_currency
        self._currency_type = currency_type
        self._owns_primary_residence = owns_primary_residence
        self._primary_residence_value = primary_residence_value

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

    def __repr__(self) -> str:
        base_repr = f"NetWorth(chain_code={self.chain_code!r}, liquid_currency={self.liquid_currency}, currency_type={self.currency_type!r}"
        if self.owns_primary_residence is not None:
            base_repr += f", owns_primary_residence={self.owns_primary_residence!r}"
        if self.primary_residence_value is not None:
            base_repr += f", primary_residence_value={self.primary_residence_value!r}"
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

    # Generate primary residence ownership if configured
    owns_primary_residence = None
    primary_residence_value = None
    if (
        config.profession_has_primary_residence is not None
        and character.profession in config.profession_has_primary_residence
    ):
        residence_config = config.profession_has_primary_residence[character.profession]
        field_value = getattr(character, residence_config.field_name)
        probability = evaluate_function(residence_config.mean_function, field_value)
        # Ensure probability is between 0 and 1
        probability = max(0.0, min(1.0, probability))
        owns_primary_residence = random.random() < probability

        # If they own a residence, generate its value
        if (
            owns_primary_residence
            and config.profession_primary_residence_value is not None
        ):
            if character.profession in config.profession_primary_residence_value:
                value_config = config.profession_primary_residence_value[
                    character.profession
                ]
                field_value = getattr(character, value_config.field_name)
                config_dict = value_config.model_dump()
                config_dict["type"] = "function_based"
                primary_residence_value = sample_from_config(config_dict, field_value)
                # Ensure the value is positive
                primary_residence_value = max(0, primary_residence_value)

    return NetWorth(
        chain_code=character.chain_code,
        liquid_currency=liquid_currency,
        currency_type=currency_type,
        owns_primary_residence=owns_primary_residence,
        primary_residence_value=primary_residence_value,
    )
