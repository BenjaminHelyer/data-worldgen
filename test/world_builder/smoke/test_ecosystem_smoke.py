from pathlib import Path

from world_builder import load_ecosystem_config, create_animal


def test_ecosystem_micro_config():
    """
    Smoke test for the ecosystem module.
    Tests the ecosystem module with a micro configuration file.
    """
    current_dir = Path(__file__).resolve().parent.parent
    config_dir = current_dir / "config"

    # Load ecosystem config
    ECOSYSTEM_CONFIG = config_dir / "ecosystem_config_micro.json"
    ECOSYSTEM_SIZE = 10

    # Load config
    ecosystem_config = load_ecosystem_config(ECOSYSTEM_CONFIG)

    # Generate ecosystem
    animals = [create_animal(ecosystem_config) for _ in range(ECOSYSTEM_SIZE)]
    assert len(animals) == ECOSYSTEM_SIZE

    # Verify animal properties
    for animal in animals:
        assert isinstance(animal.species, str)
        assert isinstance(animal.habitat, str)
        assert isinstance(animal.age, (int, float))
        assert animal.age >= 0, "Age should be non-negative"
        assert isinstance(animal.animal_id, str)
        assert animal.animal_id.startswith("AN-")
        assert animal.ecosystem == "Test Reserve"
