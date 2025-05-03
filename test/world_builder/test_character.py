import re
from uuid import UUID

import pytest

from world_builder.character import (
    _assign_names,
    _assign_chain_code,
    _assign_metadata,
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
        {"species": "ithorian", "gender": "nonbinary"},  # fallback to male generator
    ],
)
def test_assign_names_fields_present(sampled):
    _assign_names(sampled)

    assert "first_name" in sampled
    assert "surname" in sampled
    assert isinstance(sampled["first_name"], str) and sampled["first_name"].strip()
    assert isinstance(sampled["surname"], str) and sampled["surname"].strip()
