from pathlib import Path

from world_builder import load_config, create_character
from world_builder.net_worth_config import load_config as load_net_worth_config
from world_builder.net_worth_generator import generate_net_worth


def test_micro_config():
    """
    Smoke test for the world_builder module.
    Tests the world_builder module with a micro configuration file.
    Also tests net worth generation for each character.
    """
    current_dir = Path(__file__).resolve().parent.parent
    config_dir = current_dir / "config"

    # Load population config
    POPULATION_CONFIG = config_dir / "wb_config_micro.json"
    POPULATION_SIZE = 10

    # Load net worth config
    NET_WORTH_CONFIG = config_dir / "nw_config_micro_jedi.json"

    # Load both configs
    population_config = load_config(POPULATION_CONFIG)
    net_worth_config = load_net_worth_config(NET_WORTH_CONFIG)

    # Generate population
    population = [create_character(population_config) for _ in range(POPULATION_SIZE)]
    assert len(population) == POPULATION_SIZE

    # Generate net worth for each character
    net_worths = [
        generate_net_worth(character, net_worth_config) for character in population
    ]
    assert len(net_worths) == POPULATION_SIZE

    # Verify net worth properties
    for character, net_worth in zip(population, net_worths):
        assert isinstance(net_worth.liquid_currency, float)
        assert net_worth.currency_type == "credits"

        # With constant functions, mean is 1000 and std is 100
        # Allow for 5 standard deviations of variation
        assert 500 <= net_worth.liquid_currency <= 1500


def test_large_config():
    """
    Smoke test for the world_builder module using the large configuration files.
    Tests character generation and net worth calculation for a larger population.
    """
    current_dir = Path(__file__).resolve().parent.parent
    config_dir = current_dir / "config"

    # Load population config
    POPULATION_CONFIG = config_dir / "wb_config_large.json"
    POPULATION_SIZE = 1000

    # Load net worth config
    NET_WORTH_CONFIG = config_dir / "nw_config_large.json"

    # Load both configs
    population_config = load_config(POPULATION_CONFIG)
    net_worth_config = load_net_worth_config(NET_WORTH_CONFIG)

    # Generate population
    population = [create_character(population_config) for _ in range(POPULATION_SIZE)]
    assert len(population) == POPULATION_SIZE

    # Generate net worth for each character
    net_worths = [
        generate_net_worth(character, net_worth_config) for character in population
    ]
    assert len(net_worths) == POPULATION_SIZE

    # Just verify the basic types are correct
    for character, net_worth in zip(population, net_worths):
        assert hasattr(
            net_worth, "liquid_currency"
        ), "Net worth missing liquid_currency"
        assert hasattr(net_worth, "currency_type"), "Net worth missing currency_type"
        assert isinstance(
            net_worth.liquid_currency, (int, float)
        ), "Net worth not numeric"
        assert isinstance(net_worth.currency_type, str), "Currency type not string"
