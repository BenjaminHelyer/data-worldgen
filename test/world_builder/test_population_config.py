from pathlib import Path

import pytest
from pydantic import ValidationError

from world_builder.population_config import load_config, PopulationConfig

parent_dir = Path(__file__).resolve().parent
CONFIG_DIR = parent_dir / "config"
CONFIG_FILE = CONFIG_DIR / "wb_config_micro.json"


@pytest.mark.parametrize(
    "filename",
    [
        "wb_config_micro.json",
        "wb_config_small.json",
    ],  # known good configs -- should pass
)
def test_load_config_smoke(filename):
    """
    Smoke test: ensure that loading a known good config file works without errors.
    """
    config_path = CONFIG_DIR / filename
    config = load_config(config_path)
    assert config is not None
    assert config.planet is not None
    assert isinstance(config.city_base_probability, dict)


@pytest.mark.parametrize(
    "filename",
    [
        "wb_config_bad_weights_profession.json"
    ],  # intentionally broken config -- profession weights don't sum to 1.0
)
def test_load_config_bad_weights(filename):
    """
    Test that loading a config with invalid weights fails validation.
    """
    config_path = CONFIG_DIR / filename

    with pytest.raises(ValidationError):
        _ = load_config(config_path)


@pytest.mark.parametrize(
    "filename",
    [
        "wb_config_bad_factors.json"
    ],  # intentionally broken config -- factors are negative
)
def test_load_config_bad_factors(filename):
    """
    Test that loading a config with invalid factors fails validation.
    """
    config_path = CONFIG_DIR / filename
    with pytest.raises(ValidationError):
        _ = load_config(config_path)


# the below tests are for PopulationConfig directly, without loading a file
# this enables us to more granually tweak options without burdening the codebase with a multiplicity of config files

good_configs = [
    # test for data without factors
    {
        "planet": "Tatooine",
        "city_base_probability": {"Mos Eisley": 1.0},
        "species_base_probability": {"human": 1.0},
        "profession_base_probability": {"Jedi": 1.0},
        "allegiance_base_probability": {"Rebel": 0.5, "Neutral": 0.5},
        "gender_base_probability": {"male": 0.5, "female": 0.5},
        "age_distribution": {"type": "normal", "mean": 35, "std": 20},
    },
    # test for data with factors
    {
        "planet": "Tatooine",
        "city_base_probability": {"Mos Eisley": 1.0},
        "species_base_probability": {"human": 1.0},
        "profession_base_probability": {"Jedi": 1.0},
        "allegiance_base_probability": {"Rebel": 0.5, "Neutral": 0.5},
        "gender_base_probability": {"male": 0.5, "female": 0.5},
        "age_distribution": {"type": "normal", "mean": 35, "std": 20},
        "factors": {"city": {"allegiance": {"Mos Eisley": {"Rebel": 2.0}}}},
    },
]

bad_configs = [
    # base probabilities sum != 1.0
    {
        "planet": "Tatooine",
        "city_base_probability": {"Mos Eisley": 0.8, "Anchorhead": 0.3},
        "species_base_probability": {"human": 1.0},
        "profession_base_probability": {"Jedi": 1.0},
        "allegiance_base_probability": {"Rebel": 0.5, "Neutral": 0.5},
        "gender_base_probability": {"male": 0.5, "female": 0.5},
        "age_distribution": {"type": "normal", "mean": 35, "std": 20},
    },
    # negative factor multiplier
    {
        "planet": "Tatooine",
        "city_base_probability": {"Mos Eisley": 1.0},
        "species_base_probability": {"human": 1.0},
        "profession_base_probability": {"Jedi": 1.0},
        "allegiance_base_probability": {"Rebel": 0.5, "Neutral": 0.5},
        "gender_base_probability": {"male": 0.5, "female": 0.5},
        "age_distribution": {"type": "normal", "mean": 35, "std": 20},
        "factors": {"city": {"allegiance": {"Mos Eisley": {"Rebel": -1.0}}}},
    },
    # factors wrong shape (non-dict dimension)
    {
        "planet": "Tatooine",
        "city_base_probability": {"Mos Eisley": 1.0},
        "species_base_probability": {"human": 1.0},
        "profession_base_probability": {"Jedi": 1.0},
        "allegiance_base_probability": {"Rebel": 0.5, "Neutral": 0.5},
        "gender_base_probability": {"male": 0.5, "female": 0.5},
        "age_distribution": {"type": "normal", "mean": 35, "std": 20},
        "factors": {"city": "invalid"},
    },
]


@pytest.mark.parametrize("config_data", good_configs)
def test_populationconfig_valid(config_data):
    """
    Valid PopulationConfig data should instantiate without errors.
    """
    config = PopulationConfig(**config_data)
    assert config.planet == config_data["planet"]
    assert isinstance(config.city_base_probability, dict)


@pytest.mark.parametrize("config_data", bad_configs)
def test_populationconfig_invalid(config_data):
    """
    Invalid PopulationConfig data should raise ValidationError.
    """
    with pytest.raises(ValidationError):
        PopulationConfig(**config_data)
