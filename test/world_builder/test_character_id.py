"""Test for the character_id module."""

from uuid import UUID

import pytest

from world_builder.population.character_id import generate_character_id, generate_uuidv7


def test_generate_uuidv7_smoke():
    """Test the generate_uuidv7 function to see if it even runs."""
    uuid = generate_uuidv7()
    assert isinstance(uuid, UUID)


def test_generate_character_id_smoke():
    """
    Test the generate_character_id function to see if it even runs.
    """
    character_id = generate_character_id("human", True)
    assert isinstance(character_id, str)
    assert len(character_id) > 0


def test_generate_uuidv7_uniqueness():
    """Test that generate_uuidv7 produces unique UUIDs."""
    uuids = [generate_uuidv7() for _ in range(100)]
    assert len(uuids) == len(set(uuids)), "UUIDs should be unique"
