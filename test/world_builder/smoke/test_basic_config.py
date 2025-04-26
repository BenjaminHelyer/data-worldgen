from pathlib import Path

from world_builder import load_config, create_character

def test_micro_config():
    """
    Smoke test for the world_builder module.
    Tests the world_builder module with a micro configuration file.
    """
    current_dir = Path(__file__).resolve().parent
    config_dir = current_dir / "config"

    CONFIG_FILE = config_dir / "wb_config_micro.json"
    POPULATION_SIZE = 10

    # loading the config takes some logic as well
    # so this will also smoke if something is broken in load_config
    config = load_config(CONFIG_FILE)

    # we just want to run the create_character function for the population size
    # if it smokes here, that means something is fried inside
    # if it doesn't smoke -- and we get the expected number of objects -- then the test passes
    population = [create_character(config) for _ in range(POPULATION_SIZE)]

    assert len(population) == POPULATION_SIZE

