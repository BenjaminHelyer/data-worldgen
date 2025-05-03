from uuid import UUID
from types import SimpleNamespace

import pytest

from world_builder.character import (
    _assign_names,
    _assign_chain_code,
    _assign_metadata,
    _sample_finite_fields,
)


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
def test_assign_chain_code_format(species, gender_prefix):
    gender = (
        "female" if gender_prefix == "F" else "male" if gender_prefix == "M" else None
    )
    sampled = {"species": species}
    if gender:
        sampled["gender"] = gender

    _assign_chain_code(sampled)

    chain_code = sampled.get("chain_code")
    assert chain_code is not None
    assert chain_code.startswith("CC-")

    # Validate UUID portion
    parts = chain_code.split("-")
    assert len(parts) >= 6  # CC-SPECIES-G-UUID
    uuid_part = "-".join(parts[-5:])
    try:
        UUID(uuid_part)
    except ValueError:
        pytest.fail(f"Invalid UUID portion in chain code: {uuid_part}")


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
    sampled = _sample_finite_fields(config)

    assert set(sampled.keys()) == set(expected_keys)
    for key in expected_keys:
        assert sampled[key] in expected_choices[key]
