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
    for net_worth in net_worths:
        assert isinstance(net_worth.liquid_currency, float)
        assert net_worth.currency_type == "credits"
        # Verify that the net worth is within reasonable bounds for a Jedi
        # Using 5 standard deviations as a reasonable bound
        assert 400 <= net_worth.liquid_currency <= 1600  # mean ± 5*std
