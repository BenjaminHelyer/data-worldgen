from uuid import UUID
from types import SimpleNamespace
from typing_extensions import Dict, Any
from collections import Counter

import pytest
import numpy as np

from world_builder.ecosystem.animal import (
    _assign_animal_id,
    _assign_metadata,
    Animal,
    create_animal,
)
from world_builder.core.sampling import (
    sample_finite_fields as _sample_finite_fields,
    sample_distribution_fields_with_overrides as _sample_distribution_fields_with_overrides,
)
from world_builder.distributions_config import (
    NormalDist,
    DistributionTransformOperation,
)
from world_builder.ecosystem.config import EcosystemConfig


@pytest.mark.parametrize(
    "metadata, expected_keys",
    [
        ({"ecosystem": "Northwood Reserve"}, ["ecosystem"]),
        (
            {"ecosystem": "Northwood Reserve", "region": "Northern Forest"},
            ["ecosystem", "region"],
        ),
        ({}, []),  # no metadata
    ],
)
def test_assign_metadata_adds_expected_keys(metadata, expected_keys):
    sampled = {}
    config = type("Config", (), {"metadata": metadata})()

    _assign_metadata(sampled, config)

    for key in expected_keys:
        assert key in sampled
        assert sampled[key] == metadata[key]


@pytest.mark.parametrize(
    "species, habitat_prefix",
    [
        ("fox", "FOR"),
        ("rabbit", "GRA"),
        ("hawk", "WET"),
        ("", "FOR"),  # missing species should still generate
        ("fox", ""),  # missing habitat should still generate
    ],
)
def test_assign_animal_id_format(species, habitat_prefix):
    sampled = {
        "species": species,
        "habitat": habitat_prefix.lower() if habitat_prefix else "",
    }
    _assign_animal_id(sampled)
    assert "animal_id" in sampled
    assert isinstance(sampled["animal_id"], str)
    assert sampled["animal_id"].startswith("AN-")


def test_animal_creation():
    """Test that Animal can be created with dynamic attributes."""
    animal = Animal(species="fox", habitat="forest", age=5)
    assert animal.species == "fox"
    assert animal.habitat == "forest"
    assert animal.age == 5


def test_animal_repr():
    """Test that Animal has a useful string representation."""
    animal = Animal(species="fox", habitat="forest", age=5)
    repr_str = repr(animal)
    assert "Animal" in repr_str
    assert "fox" in repr_str
    assert "forest" in repr_str


def test_create_animal_smoke():
    """Smoke test for create_animal function."""
    config_data = {
        "base_probabilities_finite": {
            "species": {"fox": 1.0},
            "habitat": {"forest": 1.0},
        },
        "base_probabilities_distributions": {
            "age": {"type": "truncated_normal", "mean": 5, "std": 2, "lower": 0}
        },
        "metadata": {"ecosystem": "Test Reserve"},
    }
    config = EcosystemConfig(**config_data)
    animal = create_animal(config)
    assert isinstance(animal, Animal)
    assert animal.species == "fox"
    assert animal.habitat == "forest"
    assert "animal_id" in animal.__dict__
    assert animal.ecosystem == "Test Reserve"


def test_create_animal_with_factors():
    """Test animal creation with factor graph."""
    config_data = {
        "base_probabilities_finite": {
            "habitat": {"forest": 0.5, "grassland": 0.5},
            "species": {"fox": 0.5, "rabbit": 0.5},
        },
        "base_probabilities_distributions": {
            "age": {"type": "truncated_normal", "mean": 5, "std": 2, "lower": 0}
        },
        "factors": {"habitat": {"species": {"forest": {"fox": 2.0}}}},
        "metadata": {},
    }
    config = EcosystemConfig(**config_data)

    # Generate many animals and check that factors are working
    animals = [create_animal(config) for _ in range(100)]
    forest_animals = [a for a in animals if a.habitat == "forest"]
    forest_foxes = [a for a in forest_animals if a.species == "fox"]

    # With factor of 2.0, we should see more foxes in forest
    fox_ratio = len(forest_foxes) / len(forest_animals) if forest_animals else 0
    assert (
        fox_ratio > 0.5
    ), f"Expected more foxes in forest due to factor, got {fox_ratio}"


def test_create_animal_with_transforms():
    """Test animal creation with distribution transforms."""
    config_data = {
        "base_probabilities_finite": {
            "species": {"fox": 1.0},
            "habitat": {"forest": 1.0},
        },
        "base_probabilities_distributions": {
            "age": {"type": "truncated_normal", "mean": 5, "std": 2, "lower": 0},
        },
        "metadata": {},
    }
    config = EcosystemConfig(**config_data)

    animals = [create_animal(config) for _ in range(100)]
    ages = [a.age for a in animals]

    # Check that values are reasonable
    # Ages should be positive (using truncated_normal with lower=0)
    assert all(age >= 0 for age in ages), "Ages should be non-negative"
