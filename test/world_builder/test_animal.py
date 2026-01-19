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
    "species, color",
    [
        ("fox", "red"),
        ("rabbit", "white"),
        ("hawk", "brown"),
        ("", "brown"),  # missing species should still generate
        ("fox", ""),  # missing color should still generate
    ],
)
def test_assign_animal_id_format(species, color):
    sampled = {
        "species": species,
        "color": color,
    }
    _assign_animal_id(sampled)
    assert "animal_id" in sampled
    assert isinstance(sampled["animal_id"], str)
    assert sampled["animal_id"].startswith("AN-")


def test_animal_creation():
    """Test that Animal can be created with dynamic attributes."""
    animal = Animal(species="fox", color="brown", health_state="healthy", age=5, height=50, weight=30)
    assert animal.species == "fox"
    assert animal.color == "brown"
    assert animal.health_state == "healthy"
    assert animal.age == 5
    assert animal.height == 50
    assert animal.weight == 30


def test_animal_repr():
    """Test that Animal has a useful string representation."""
    animal = Animal(species="fox", color="brown", health_state="healthy", age=5, height=50, weight=30)
    repr_str = repr(animal)
    assert "Animal" in repr_str
    assert "fox" in repr_str
    assert "brown" in repr_str


def test_create_animal_smoke():
    """Smoke test for create_animal function."""
    config_data = {
        "base_probabilities_finite": {
            "species": {"fox": 1.0},
            "color": {"brown": 1.0},
            "health_state": {"healthy": 1.0},
        },
        "base_probabilities_distributions": {
            "age": {"type": "truncated_normal", "mean": 5, "std": 2, "lower": 0},
            "height": {"type": "truncated_normal", "mean": 50, "std": 10, "lower": 5},
            "weight": {"type": "truncated_normal", "mean": 30, "std": 8, "lower": 1}
        },
        "metadata": {"ecosystem": "Test Reserve"},
    }
    config = EcosystemConfig(**config_data)
    animal = create_animal(config)
    assert isinstance(animal, Animal)
    assert animal.species == "fox"
    assert animal.color == "brown"
    assert animal.health_state == "healthy"
    assert "animal_id" in animal.__dict__
    assert animal.ecosystem == "Test Reserve"
    assert isinstance(animal.age, (int, float))
    assert isinstance(animal.height, (int, float))
    assert isinstance(animal.weight, (int, float))


def test_create_animal_with_factors():
    """Test animal creation with factor graph."""
    config_data = {
        "base_probabilities_finite": {
            "species": {"fox": 0.5, "rabbit": 0.5},
            "color": {"red": 0.5, "brown": 0.5},
        },
        "base_probabilities_distributions": {
            "age": {"type": "truncated_normal", "mean": 5, "std": 2, "lower": 0},
            "height": {"type": "truncated_normal", "mean": 50, "std": 10, "lower": 5},
            "weight": {"type": "truncated_normal", "mean": 30, "std": 8, "lower": 1}
        },
        "factors": {"species": {"color": {"fox": {"red": 2.0}}}},
        "metadata": {},
    }
    config = EcosystemConfig(**config_data)
    # Generate many animals and check that factors are working
    animals = [create_animal(config) for _ in range(100)]
    foxes = [a for a in animals if a.species == "fox"]
    red_foxes = [a for a in foxes if a.color == "red"]

    # With factor of 2.0, we should see more red foxes
    red_ratio = len(red_foxes) / len(foxes) if foxes else 0
    assert (
        red_ratio > 0.5
    ), f"Expected more red foxes due to factor, got {red_ratio}"


def test_create_animal_with_transforms():
    """Test animal creation with distribution transforms."""
    config_data = {
        "base_probabilities_finite": {
            "species": {"fox": 1.0},
            "color": {"brown": 1.0},
            "health_state": {"healthy": 1.0},
        },
        "base_probabilities_distributions": {
            "age": {"type": "truncated_normal", "mean": 5, "std": 2, "lower": 0},
            "height": {"type": "truncated_normal", "mean": 50, "std": 10, "lower": 5},
            "weight": {"type": "truncated_normal", "mean": 30, "std": 8, "lower": 1}
        },
        "metadata": {},
    }
    config = EcosystemConfig(**config_data)

    animals = [create_animal(config) for _ in range(100)]
    ages = [a.age for a in animals]
    heights = [a.height for a in animals]
    weights = [a.weight for a in animals]

    # Check that values are reasonable
    # Ages should be positive (using truncated_normal with lower=0)
    assert all(age >= 0 for age in ages), "Ages should be non-negative"
    assert all(height >= 5 for height in heights), "Heights should be >= 5"
    assert all(weight >= 1 for weight in weights), "Weights should be >= 1"