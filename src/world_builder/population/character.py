"""
Character generation for population domain.

This module provides character creation using the generic sampling functions
from core.sampling, along with population-specific post-processing (names, character IDs).
"""

from typing import Any, Dict

from world_builder.core.sampling import (
    sample_finite_fields,
    sample_distribution_fields_with_overrides,
)
from world_builder.population.config import PopulationConfig
from world_builder.population.character_id import generate_character_id

from namegen import (
    generate_female_first_name,
    generate_male_first_name,
    generate_surname,
)


class Character:
    """
    Represents a character with dynamically assigned attributes.

    Attributes are assigned via keyword arguments during initialization,
    allowing for flexible character definitions based on configuration.
    """

    def __init__(self, **attributes: Any):
        """
        Constructor for the character class, in which attributes are assigned dynamically
        via the passed-in dictionary.
        """
        # assign attributes dynamically by passing in a dict of attributes
        for name, value in attributes.items():
            setattr(self, name, value)

    def __repr__(self) -> str:
        """
        Returns the string representation of the Character.

        Example representation:
            Character(species='human', age=42).
        """
        props = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"Character({props})"


def _assign_metadata(sampled: Dict[str, Any], config: PopulationConfig) -> None:
    """
    Assigns constant metadata fields to the character.

    Metadata is an optional dictionary specified in the config, consisting of string key-value pairs.
    These fields are not sampled probabilistically; they are copied directly as constants into the character.
    Common use cases might include static identifiers like planet name, data version, or authoring info.

    Example:
        config.metadata = {"planet": "Tatooine", "author": "Obi-Wan"}
        ➞ sampled["planet"] = "Tatooine"
           sampled["author"] = "Obi-Wan"
    """
    for field_name, field_value in config.metadata.items():
        sampled[field_name] = field_value


def _assign_character_id(sampled: Dict[str, Any]) -> None:
    """
    Generates and assigns a unique character_id to the character.

    The character_id is a UUIDv7-like identifier encoding species and gender information.
    It is useful for later tracing or decoding metadata about the character.

    Format (example):
        "CC-HUM-M-0196940f-92d3-7000-97b8-f3f9cf01b7f3"

    Components:
        - "CC" prefix
        - Species abbreviation (e.g., "HUM" for human, "ROD" for rodian)
        - Gender abbreviation ("M" or "F")
        - A UUIDv7-like suffix that encodes time-based uniqueness

    The species and gender are pulled from the sampled fields. If missing, defaults are blank.
    """
    species = sampled.get("species", "")
    is_female = str(sampled.get("gender", "")).lower() == "female"
    sampled["character_id"] = generate_character_id(species, is_female)


def _assign_names(sampled: Dict[str, Any]) -> None:
    """
    Generates and assigns a first name and surname for the character.

    Name generation is performed using a generative model (e.g., a Markov chain),
    trained separately for male and female first names, and for surnames by species.

    Details:
        - First name is generated using either `generate_female_first_name()` or
          `generate_male_first_name()` based on the gender field.
        - Surname is generated using `generate_surname(species=...)`, allowing species-specific naming patterns.

    These generative functions ensure name plausibility while allowing creative variation.

    Example output:
        - first_name: "Sa" (generated for female)
        - surname: "Saokaell" (generated for a human)
    """
    species = sampled.get("species", "")
    is_female = str(sampled.get("gender", "")).lower() == "female"
    sampled["first_name"] = (
        generate_female_first_name() if is_female else generate_male_first_name()
    )
    sampled["surname"] = generate_surname(species=species)


def create_character(config: PopulationConfig) -> Character:
    """
    Factory for Character. Samples discrete categories in the order specified
    by the 'factors' keys (respecting dependencies), then applies distribution-based
    sampling with optional conditional overrides, and fills metadata + names.
    """
    sampled: Dict[str, Any] = {}

    # use generic sampling functions from core
    sample_finite_fields(config, sampled)
    sample_distribution_fields_with_overrides(config, sampled)

    # apply population-specific post-processing
    _assign_character_id(sampled)
    _assign_names(sampled)
    _assign_metadata(sampled, config)

    return Character(**sampled)
