"""
Animal generation for ecosystem domain.

This module provides animal creation using the generic sampling functions
from core.sampling, along with ecosystem-specific post-processing (animal IDs).
"""

from typing import Any, Dict

from world_builder.core.sampling import (
    sample_finite_fields,
    sample_distribution_fields_with_overrides,
)
from world_builder.ecosystem.config import EcosystemConfig
from world_builder.ecosystem.animal_id import generate_animal_id


class Animal:
    """
    Represents an animal with dynamically assigned attributes.

    Attributes are assigned via keyword arguments during initialization,
    allowing for flexible animal definitions based on configuration.
    """

    def __init__(self, **attributes: Any):
        """
        Constructor for the animal class, in which attributes are assigned dynamically
        via the passed-in dictionary.
        """
        # assign attributes dynamically by passing in a dict of attributes
        for name, value in attributes.items():
            setattr(self, name, value)

    def __repr__(self) -> str:
        """
        Returns the string representation of the Animal.

        Example representation:
            Animal(species='fox', habitat='forest', age=3).
        """
        props = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"Animal({props})"


def _assign_metadata(sampled: Dict[str, Any], config: EcosystemConfig) -> None:
    """
    Assigns constant metadata fields to the animal.

    Metadata is an optional dictionary specified in the config, consisting of string key-value pairs.
    These fields are not sampled probabilistically; they are copied directly as constants into the animal.
    Common use cases might include static identifiers like ecosystem name, region, or data version.

    Example:
        config.metadata = {"ecosystem": "Northwood Reserve", "region": "Northern Forest"}
        ➞ sampled["ecosystem"] = "Northwood Reserve"
           sampled["region"] = "Northern Forest"
    """
    for field_name, field_value in config.metadata.items():
        sampled[field_name] = field_value


def _assign_animal_id(sampled: Dict[str, Any]) -> None:
    """
    Generates and assigns a unique animal_id to the animal.

    The animal_id is a UUIDv7-like identifier encoding species and habitat information.
    It is useful for later tracing or decoding metadata about the animal.

    Format (example):
        "AN-FOX-FOR-0196940f-92d3-7000-97b8-f3f9cf01b7f3"

    Components:
        - "AN" prefix (Animal)
        - Species abbreviation (e.g., "FOX" for fox, "HAW" for hawk)
        - Habitat abbreviation (e.g., "FOR" for forest, "WET" for wetland)
        - A UUIDv7-like suffix that encodes time-based uniqueness

    The species and habitat are pulled from the sampled fields. If missing, defaults are blank.
    """
    species = sampled.get("species", "")
    habitat = sampled.get("habitat", "")
    sampled["animal_id"] = generate_animal_id(species, habitat)


def create_animal(config: EcosystemConfig) -> Animal:
    """
    Factory for Animal. Samples discrete categories in the order specified
    by the 'factors' keys (respecting dependencies), then applies distribution-based
    sampling with optional conditional overrides, and fills metadata + animal ID.
    """
    sampled: Dict[str, Any] = {}

    # use generic sampling functions from core
    sample_finite_fields(config, sampled)
    sample_distribution_fields_with_overrides(config, sampled)

    # apply ecosystem-specific post-processing
    _assign_animal_id(sampled)
    _assign_metadata(sampled, config)

    return Animal(**sampled)
