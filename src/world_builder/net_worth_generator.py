"""
Module for generating net worth values for characters based on their professions.
"""

from dataclasses import dataclass
from typing import Optional

from world_builder.net_worth_config import NetWorthConfig
from world_builder.distributions_config import sample_from_config
from world_builder.character import Character


class NetWorth:
    """
    Represents a character's net worth.

    Attributes:
        chain_code: The unique identifier for this net worth record
        liquid_currency: The amount of liquid currency the character has
        currency_type: The type of currency (e.g., "credits", "imperial_credits")
    """

    def __init__(self, chain_code: str, liquid_currency: float, currency_type: str):
        self._chain_code = chain_code
        self._liquid_currency = liquid_currency
        self._currency_type = currency_type

    @property
    def chain_code(self) -> str:
        return self._chain_code

    @property
    def liquid_currency(self) -> float:
        return self._liquid_currency

    @property
    def currency_type(self) -> str:
        return self._currency_type

    def __repr__(self) -> str:
        return f"NetWorth(chain_code={self.chain_code!r}, liquid_currency={self.liquid_currency}, currency_type={self.currency_type!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NetWorth):
            return NotImplemented
        return (
            self.chain_code == other.chain_code
            and self.liquid_currency == other.liquid_currency
            and self.currency_type == other.currency_type
        )


def generate_net_worth(character: Character, config: NetWorthConfig) -> NetWorth:
    """
    Generate a net worth value for a character based on their profession.

    Args:
        character: The character to generate net worth for
        config: The net worth configuration containing profession-based distributions

    Returns:
        A NetWorth object with the generated values

    Raises:
        ValueError: If the character's profession is not found in the config
    """
    if character.profession not in config.profession_net_worth:
        raise ValueError(
            f"Character profession '{character.profession}' not found in net worth config"
        )

    # Get the distribution for this profession
    dist_config = config.profession_net_worth[character.profession]

    # Sample from the distribution
    liquid_currency = sample_from_config(dist_config)

    # Get currency type from metadata, defaulting to "credits" if not specified
    currency_type = config.metadata.get("currency", "credits")

    return NetWorth(
        chain_code=character.chain_code,
        liquid_currency=liquid_currency,
        currency_type=currency_type,
    )
