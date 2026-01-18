from uuid import UUID
from types import SimpleNamespace
from typing_extensions import Dict, Any
from collections import Counter

import pytest
import numpy as np

from world_builder.population.character import (
    _assign_names,
    _assign_character_id,
    _assign_metadata,
)
from world_builder.core.sampling import (
    sample_finite_fields as _sample_finite_fields,
    sample_distribution_fields_with_overrides as _sample_distribution_fields_with_overrides,
)
from world_builder.distributions_config import (
    NormalDist,
    DistributionTransformOperation,
)
from world_builder.population.config import PopulationConfig


@pytest.mark.parametrize(
    "metadata, expected_keys",
    [
        ({"planet": "Tatooine"}, ["planet"]),
        ({"planet": "Naboo", "version": "v2.1"}, ["planet", "version"]),
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
    "species, gender_prefix",
    [
        ("human", "M"),
        ("wookiee", "F"),
        ("twilek", ""),  # missing gender should still generate
        ("", "M"),  # missing species should still genderate
        ("", ""),  # both missing gender and missing species should still generate
    ],
)
def test_assign_character_id_format(species, gender_prefix):
    gender = (
        "female" if gender_prefix == "F" else "male" if gender_prefix == "M" else None
    )
    sampled = {"species": species}
    if gender:
        sampled["gender"] = gender

    _assign_character_id(sampled)

    character_id = sampled.get("character_id")
    assert character_id is not None
    assert character_id.startswith("CC-")

    # Validate UUID portion
    parts = character_id.split("-")
    assert len(parts) >= 6  # CC-SPECIES-G-UUID
    uuid_part = "-".join(parts[-5:])
    try:
        UUID(uuid_part)
    except ValueError:
        pytest.fail(f"Invalid UUID portion in character_id: {uuid_part}")


@pytest.mark.parametrize(
    "sampled",
    [
        {"species": "zabrak", "gender": "male"},
        {"species": "twilek", "gender": "female"},
    ],
)
def test_assign_names_fields_present(sampled):
    _assign_names(sampled)

    assert "first_name" in sampled
    assert "surname" in sampled
    assert isinstance(sampled["first_name"], str) and sampled["first_name"].strip()
    assert isinstance(sampled["surname"], str) and sampled["surname"].strip()


@pytest.mark.parametrize(
    "finite_probs, factors, expected_keys, expected_choices",
    [
        # Case 1: No factors, simple uniform sampling
        (
            {"species": {"human": 0.5, "twilek": 0.5}},
            {},
            ["species"],
            {"species": {"human", "twilek"}},
        ),
        # Case 2: Factor order respected (city before allegiance)
        (
            {
                "city": {"Mos Eisley": 1.0},
                "allegiance": {"Imperial": 0.5, "Rebel": 0.5},
            },
            {"allegiance": {"city": {"Mos Eisley": {"Imperial": 10.0}}}},
            ["city", "allegiance"],
            {"city": {"Mos Eisley"}, "allegiance": {"Imperial", "Rebel"}},
        ),
        # Case 3: More than two fields with dependencies
        (
            {
                "species": {"zabrak": 1.0},
                "profession": {"warrior": 0.7, "farmer": 0.3},
                "allegiance": {"Neutral": 1.0},
            },
            {"profession": {"species": {"zabrak": {"warrior": 2.0, "farmer": 0.5}}}},
            ["species", "profession", "allegiance"],
            {
                "species": {"zabrak"},
                "profession": {"warrior", "farmer"},
                "allegiance": {"Neutral"},
            },
        ),
    ],
)
def test_sample_finite_fields(finite_probs, factors, expected_keys, expected_choices):
    config = SimpleNamespace(base_probabilities_finite=finite_probs, factors=factors)
    sampled: Dict[str, Any] = {}
    _sample_finite_fields(config, sampled)

    assert set(sampled.keys()) == set(expected_keys)
    for key in expected_keys:
        assert sampled[key] in expected_choices[key]


class DummyConfig:
    def __init__(self, base_probabilities_finite, factors):
        self.base_probabilities_finite = base_probabilities_finite
        self.factors = factors


@pytest.mark.parametrize(
    "base_probs, factors, sampled_fixed, target_field, expected_dominant",
    [
        # Case 1: Base probs are uniform, but 'city' factor gives 1000x multiplier to 'sullustan'
        (
            {
                "species": {
                    "sullustan": 0.2,
                    "zabrak": 0.2,
                    "trandoshan": 0.2,
                    "rodian": 0.2,
                    "moncal": 0.2,
                }
            },
            {
                "city": {
                    "species": {
                        "Mos Eisley": {
                            "sullustan": 1000.0,
                            "zabrak": 1.0,
                            "trandoshan": 1.0,
                            "rodian": 1.0,
                            "moncal": 1.0,
                        }
                    }
                }
            },
            {"city": "Mos Eisley"},
            "species",
            "sullustan",
        ),
        # Case 2: No influencing factor, so uniform distribution expected
        (
            {
                "species": {
                    "sullustan": 0.25,
                    "zabrak": 0.25,
                    "trandoshan": 0.25,
                    "rodian": 0.25,
                }
            },
            {},
            {},
            "species",
            None,  # No dominant outcome expected
        ),
        # Case 3: Factor favors 'moncal' by a large margin
        (
            {
                "species": {
                    "sullustan": 0.1,
                    "zabrak": 0.1,
                    "trandoshan": 0.1,
                    "rodian": 0.1,
                    "moncal": 0.6,
                }
            },
            {"planet": {"species": {"Dac": {"moncal": 1000.0}}}},
            {"planet": "Dac"},
            "species",
            "moncal",
        ),
    ],
)
def test_sample_finite_fields_respects_factors(
    base_probs, factors, sampled_fixed, target_field, expected_dominant
):
    NUM_SAMPLES = 500
    config = DummyConfig(base_probabilities_finite=base_probs, factors=factors)

    def wrapped_sampler():
        sampled = sampled_fixed.copy()
        _sample_finite_fields(config, sampled)
        return sampled[target_field]

    results = Counter(wrapped_sampler() for _ in range(NUM_SAMPLES))

    if expected_dominant:
        dominant_ratio = results[expected_dominant] / NUM_SAMPLES
        assert (
            dominant_ratio > 0.8
        ), f"Expected '{expected_dominant}' to dominate, got ratio {dominant_ratio:.2f}"
    else:
        expected_count = NUM_SAMPLES / len(base_probs[target_field])
        for k in base_probs[target_field]:
            count = results[k]
            ratio = count / expected_count
            assert (
                0.7 < ratio < 1.3
            ), f"Expected near-uniform distribution for '{k}', got ratio {ratio:.2f}"


@pytest.mark.parametrize(
    "base_dist, transform, sampled_fixed, expected_mean_threshold",
    [
        # mean_shift of +1000 should drastically raise mean
        (
            NormalDist(type="normal", mean=-25.0, std=0.01),
            {"species": {"Giant": DistributionTransformOperation(mean_shift=1000)}},
            {"species": "Giant"},
            800.0,  # expect mean to be well above this
        )
    ],
)
def test_sample_distribution_transform_effects(
    base_dist, transform, sampled_fixed, expected_mean_threshold
):
    NUM_SAMPLES = 500
    config = PopulationConfig(
        base_probabilities_finite={"species": {sampled_fixed["species"]: 1.0}},
        base_probabilities_distributions={"age": base_dist},
        factors={},
        override_distributions=[],
        transform_distributions={"age": transform},
        metadata={},
    )

    samples = []
    for _ in range(NUM_SAMPLES):
        sampled = sampled_fixed.copy()
        _sample_distribution_fields_with_overrides(config, sampled)
        samples.append(sampled["age"])

    mean_result = np.mean(samples)
    assert (
        mean_result > expected_mean_threshold
    ), f"Expected mean > {expected_mean_threshold}, but got {mean_result:.2f}"
