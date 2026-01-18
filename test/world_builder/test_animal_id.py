"""Test for the animal_id module."""

from uuid import UUID

import pytest

from world_builder.ecosystem.animal_id import generate_animal_id, generate_uuidv7


def test_generate_uuidv7_smoke():
    """Test the generate_uuidv7 function to see if it even runs."""
    uuid = generate_uuidv7()
    assert isinstance(uuid, UUID)


def test_generate_animal_id_smoke():
    """
    Test the generate_animal_id function to see if it even runs.
    """
    animal_id = generate_animal_id("fox", "forest")
    assert isinstance(animal_id, str)
    assert len(animal_id) > 0


def test_generate_uuidv7_uniqueness():
    """Test that generate_uuidv7 produces unique UUIDs."""
    uuids = [generate_uuidv7() for _ in range(100)]
    assert len(uuids) == len(set(uuids)), "UUIDs should be unique"


def test_generate_animal_id_format():
    """Test that animal_id has the correct format."""
    animal_id = generate_animal_id("fox", "forest")
    assert animal_id.startswith("AN-")
    assert "FOX" in animal_id
    assert "FOR" in animal_id


def test_generate_animal_id_different_species():
    """Test that different species produce different prefixes."""
    id1 = generate_animal_id("fox", "forest")
    id2 = generate_animal_id("rabbit", "forest")
    assert id1 != id2
    assert "FOX" in id1
    assert "RAB" in id2


def test_generate_animal_id_different_habitats():
    """Test that different habitats produce different prefixes."""
    id1 = generate_animal_id("fox", "forest")
    id2 = generate_animal_id("fox", "grassland")
    assert id1 != id2
    assert "FOR" in id1
    assert "GRA" in id2
