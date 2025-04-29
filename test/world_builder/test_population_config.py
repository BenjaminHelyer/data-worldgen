from pathlib import Path

import pytest
from pydantic import ValidationError

from world_builder.population_config import load_config, PopulationConfig
from world_builder.distributions_config import Distribution

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

# Valid configurations should use the new schema keys:
good_configs = [
    # test for data without factors
    {
        "base_probabilities_finite": {
            "city": {"Mos Eisley": 1.0},
            "species": {"human": 1.0},
            "profession": {"Jedi": 1.0},
            "allegiance": {"Rebel": 0.5, "Neutral": 0.5},
            "gender": {"male": 0.5, "female": 0.5},
        },
        "base_probabilities_distributions": {
            "age": {"type": "normal", "mean": 35, "std": 20}
        },
    },
    # test for data with factors
    {
        "base_probabilities_finite": {
            "city": {"Mos Eisley": 1.0},
            "species": {"human": 1.0},
            "profession": {"Jedi": 1.0},
            "allegiance": {"Rebel": 0.5, "Neutral": 0.5},
            "gender": {"male": 0.5, "female": 0.5},
        },
        "base_probabilities_distributions": {
            "age": {"type": "normal", "mean": 35, "std": 20}
        },
        "factors": {"city": {"allegiance": {"Mos Eisley": {"Rebel": 2.0}}}},
    },
]

# Invalid configurations should trigger validation errors:
bad_configs = [
    # base probabilities sum != 1.0
    {
        "base_probabilities_finite": {
            "city": {"Mos Eisley": 0.8, "Anchorhead": 0.3},
            "species": {"human": 1.0},
            "profession": {"Jedi": 1.0},
            "allegiance": {"Rebel": 0.5, "Neutral": 0.5},
            "gender": {"male": 0.5, "female": 0.5},
        },
        "base_probabilities_distributions": {
            "age": {"type": "normal", "mean": 35, "std": 20}
        },
    },
    # negative factor multiplier
    {
        "base_probabilities_finite": {
            "city": {"Mos Eisley": 1.0},
            "species": {"human": 1.0},
            "profession": {"Jedi": 1.0},
            "allegiance": {"Rebel": 0.5, "Neutral": 0.5},
            "gender": {"male": 0.5, "female": 0.5},
        },
        "base_probabilities_distributions": {
            "age": {"type": "normal", "mean": 35, "std": 20}
        },
        "factors": {"city": {"allegiance": {"Mos Eisley": {"Rebel": -1.0}}}},
    },
    # factors wrong shape (non-dict dimension)
    {
        "base_probabilities_finite": {
            "city": {"Mos Eisley": 1.0},
            "species": {"human": 1.0},
            "profession": {"Jedi": 1.0},
            "allegiance": {"Rebel": 0.5, "Neutral": 0.5},
            "gender": {"male": 0.5, "female": 0.5},
        },
        "base_probabilities_distributions": {
            "age": {"type": "normal", "mean": 35, "std": 20}
        },
        "factors": {"city": "invalid"},
    },
]


@pytest.mark.parametrize("config_data", good_configs)
def test_populationconfig_valid(config_data):
    """
    Valid PopulationConfig data should instantiate without errors,
    and retain the correct structure.
    """
    config = PopulationConfig(**config_data)
    # finite probabilities
    assert config.base_probabilities_finite == config_data["base_probabilities_finite"]
    # distributions loaded as Distribution instances
    assert set(config.base_probabilities_distributions.keys()) == set(
        config_data["base_probabilities_distributions"].keys()
    )
    for key, dist in config.base_probabilities_distributions.items():
        assert isinstance(dist, Distribution)


@pytest.mark.parametrize("config_data", bad_configs)
def test_populationconfig_invalid(config_data):
    """
    Invalid PopulationConfig data should raise a ValidationError.
    """
    with pytest.raises(ValidationError):
        PopulationConfig(**config_data)
