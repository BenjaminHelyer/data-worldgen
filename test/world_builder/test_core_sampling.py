"""
Tests for the generic core sampling functions.

These tests verify that the generic sampling functions work correctly
with any config that implements the SamplingConfig protocol.
"""

import pytest
from typing import Dict

from world_builder.core.sampling import (
    apply_factor_multipliers,
    sample_finite_fields,
    sample_distribution_fields_with_overrides,
)
from world_builder.core.config_protocol import SamplingConfig
from world_builder.distributions_config import (
    NormalDist,
    DistributionOverride,
    DistributionTransformOperation,
)


class MockConfig:
    """Mock config that implements SamplingConfig protocol for testing."""

    def __init__(
        self,
        base_probabilities_finite: Dict[str, Dict[str, float]],
        base_probabilities_distributions: Dict[str, any],
        factors: Dict = None,
        override_distributions=None,
        transform_distributions=None,
        metadata=None,
    ):
        self.base_probabilities_finite = base_probabilities_finite
        self.base_probabilities_distributions = base_probabilities_distributions
        self.factors = factors or {}
        self.override_distributions = override_distributions
        self.transform_distributions = transform_distributions or {}
        self.metadata = metadata or {}


def test_apply_factor_multipliers_basic():
    """Test basic factor multiplier application."""
    base_probs = {"A": 0.5, "B": 0.5}
    all_factors = {
        "source": {"target": {"source_val_1": {"A": 2.0}}}  # Double probability of A
    }
    sampled_values = {"source": "source_val_1"}

    result = apply_factor_multipliers(base_probs, "target", sampled_values, all_factors)

    # A should be 2x more likely, so 0.5 * 2 = 1.0, B stays 0.5
    # Normalized: A = 1.0 / 1.5 = 0.666..., B = 0.5 / 1.5 = 0.333...
    assert abs(result["A"] - 2 / 3) < 1e-6
    assert abs(result["B"] - 1 / 3) < 1e-6


def test_apply_factor_multipliers_no_match():
    """Test factor multipliers when source value doesn't match."""
    base_probs = {"A": 0.5, "B": 0.5}
    all_factors = {"source": {"target": {"source_val_1": {"A": 2.0}}}}
    sampled_values = {"source": "source_val_2"}  # Different value

    result = apply_factor_multipliers(base_probs, "target", sampled_values, all_factors)

    # No match, so probabilities should be unchanged
    assert result["A"] == 0.5
    assert result["B"] == 0.5


def test_apply_factor_multipliers_multiple_factors():
    """Test factor multipliers with multiple influencing factors."""
    base_probs = {"A": 0.5, "B": 0.5}
    all_factors = {
        "source1": {"target": {"val1": {"A": 2.0}}},
        "source2": {"target": {"val2": {"A": 1.5}}},
    }
    sampled_values = {"source1": "val1", "source2": "val2"}

    result = apply_factor_multipliers(base_probs, "target", sampled_values, all_factors)

    # A gets 2.0x from source1, then 1.5x from source2: 0.5 * 2.0 * 1.5 = 1.5
    # B stays 0.5
    # Normalized: A = 1.5 / 2.0 = 0.75, B = 0.5 / 2.0 = 0.25
    assert abs(result["A"] - 0.75) < 1e-6
    assert abs(result["B"] - 0.25) < 1e-6


def test_sample_finite_fields_basic():
    """Test basic finite field sampling."""
    config = MockConfig(
        base_probabilities_finite={"field1": {"A": 1.0}},
        base_probabilities_distributions={},
    )
    sampled = {}

    sample_finite_fields(config, sampled)

    assert "field1" in sampled
    assert sampled["field1"] == "A"


def test_sample_finite_fields_with_factors():
    """Test finite field sampling with factor multipliers."""
    config = MockConfig(
        base_probabilities_finite={"field1": {"A": 0.5, "B": 0.5}},
        base_probabilities_distributions={},
        factors={"source": {"field1": {"source_val": {"A": 2.0}}}},
    )
    sampled = {"source": "source_val"}

    # Run multiple times to check probability distribution
    results = []
    for _ in range(100):
        test_sampled = sampled.copy()
        sample_finite_fields(config, test_sampled)
        results.append(test_sampled["field1"])

    # A should be more common due to 2x multiplier
    a_count = results.count("A")
    assert a_count > 50  # Should be more than 50% due to multiplier


def test_sample_distribution_fields_basic():
    """Test basic distribution field sampling."""
    config = MockConfig(
        base_probabilities_finite={},
        base_probabilities_distributions={
            "age": NormalDist(type="normal", mean=30, std=5)
        },
    )
    sampled = {}

    sample_distribution_fields_with_overrides(config, sampled)

    assert "age" in sampled
    assert isinstance(sampled["age"], (int, float))
    # Should be roughly around mean (30) with some variance
    assert 15 <= sampled["age"] <= 45  # 3 std devs


def test_sample_distribution_fields_with_override():
    """Test distribution field sampling with conditional override."""
    config = MockConfig(
        base_probabilities_finite={"type": {"special": 1.0}},
        base_probabilities_distributions={
            "value": NormalDist(type="normal", mean=10, std=2)
        },
        override_distributions=[
            DistributionOverride(
                condition={"type": "special"},
                field="value",
                distribution=NormalDist(type="normal", mean=100, std=2),
            )
        ],
    )
    sampled = {"type": "special"}

    sample_distribution_fields_with_overrides(config, sampled)

    assert "value" in sampled
    # Should be around 100 (override mean), not 10 (base mean)
    assert sampled["value"] > 50


def test_sample_distribution_fields_with_transform():
    """Test distribution field sampling with transformation."""
    config = MockConfig(
        base_probabilities_finite={"category": {"A": 1.0}},
        base_probabilities_distributions={
            "value": NormalDist(type="normal", mean=10, std=2)
        },
        transform_distributions={
            "value": {
                "category": {"A": DistributionTransformOperation(mean_shift=50.0)}
            }
        },
    )
    sampled = {"category": "A"}

    sample_distribution_fields_with_overrides(config, sampled)

    assert "value" in sampled
    # Should be around 60 (10 + 50 shift), not 10
    assert sampled["value"] > 40


def test_sample_finite_fields_preserves_existing():
    """Test that existing sampled values are preserved."""
    config = MockConfig(
        base_probabilities_finite={"field1": {"A": 1.0}},
        base_probabilities_distributions={},
    )
    sampled = {"field1": "B"}  # Pre-existing value

    sample_finite_fields(config, sampled)

    # Should not overwrite existing value
    assert sampled["field1"] == "B"


def test_sampling_config_protocol_compatibility():
    """Test that PopulationConfig works with generic sampling functions."""
    from world_builder.population.config import PopulationConfig

    config = PopulationConfig(
        base_probabilities_finite={"field1": {"A": 1.0}},
        base_probabilities_distributions={},
    )
    sampled = {}

    # Should work because PopulationConfig implements SamplingConfig protocol
    sample_finite_fields(config, sampled)
    sample_distribution_fields_with_overrides(config, sampled)

    assert "field1" in sampled
    assert sampled["field1"] == "A"
