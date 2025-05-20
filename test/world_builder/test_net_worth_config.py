from pathlib import Path

import pytest
from pydantic import ValidationError

from world_builder.net_worth_config import load_config, NetWorthConfig
from world_builder.distributions_config import (
    Distribution,
    NormalDist,
    LogNormalDist,
    TruncatedNormalDist,
)

parent_dir = Path(__file__).resolve().parent
CONFIG_DIR = parent_dir / "config"
CONFIG_FILE = CONFIG_DIR / "nw_config_micro.json"


@pytest.mark.parametrize(
    "filename",
    [
        "nw_config_micro.json",
    ],  # known good configs -- should pass
)
def test_load_config_smoke(filename):
    """
    Smoke test: ensure that loading a known good config file works without errors.
    """
    config_path = CONFIG_DIR / filename
    config = load_config(config_path)
    assert config is not None


# Valid configurations should use the new schema keys:
good_configs = [
    # test for basic normal distribution
    {
        "profession_net_worth": {
            "farmer": {"type": "normal", "mean": 100, "std": 20},
            "merchant": {"type": "normal", "mean": 500, "std": 100},
        },
        "metadata": {"currency": "credits"},
    },
    # test for mixed distribution types
    {
        "profession_net_worth": {
            "smuggler": {"type": "lognormal", "mean": 3.0, "std": 1.0},
            "bounty_hunter": {
                "type": "truncated_normal",
                "mean": 1000,
                "std": 200,
                "lower": 0,
            },
            "jedi": {"type": "normal", "mean": 50, "std": 10},
        },
        "metadata": {"currency": "credits", "era": "Clone Wars"},
    },
]

# Invalid configurations should trigger validation errors:
bad_configs = [
    # invalid distribution type
    {
        "profession_net_worth": {
            "farmer": {"type": "invalid", "mean": 100, "std": 20},
        },
        "metadata": {"currency": "credits"},
    },
    # missing required distribution parameters
    {
        "profession_net_worth": {
            "merchant": {"type": "normal", "mean": 500},  # missing std
        },
        "metadata": {"currency": "credits"},
    },
    # negative standard deviation
    {
        "profession_net_worth": {
            "farmer": {"type": "normal", "mean": 100, "std": -20},
        },
        "metadata": {"currency": "credits"},
    },
]


@pytest.mark.parametrize("config_data", good_configs)
def test_networthconfig_valid(config_data):
    """
    Valid NetWorthConfig data should instantiate without errors,
    and retain the correct structure.
    """
    config = NetWorthConfig(**config_data)
    # Check that distributions are loaded correctly
    assert set(config.profession_net_worth.keys()) == set(
        config_data["profession_net_worth"].keys()
    )
    for profession, dist in config.profession_net_worth.items():
        assert isinstance(dist, Distribution)
    # Check metadata
    if "metadata" in config_data:
        assert config.metadata == config_data["metadata"]


@pytest.mark.parametrize("config_data", bad_configs)
def test_networthconfig_invalid(config_data):
    """
    Invalid NetWorthConfig data should raise a ValidationError.
    """
    with pytest.raises(ValidationError):
        NetWorthConfig(**config_data)


def test_distribution_types():
    """
    Test that different distribution types are properly handled.
    """
    config = NetWorthConfig(
        profession_net_worth={
            "normal": NormalDist(type="normal", mean=100, std=20),
            "lognormal": LogNormalDist(type="lognormal", mean=3.0, std=1.0),
            "truncated": TruncatedNormalDist(
                type="truncated_normal", mean=1000, std=200, lower=0
            ),
        },
        metadata={"test": "test"},
    )

    assert isinstance(config.profession_net_worth["normal"], NormalDist)
    assert isinstance(config.profession_net_worth["lognormal"], LogNormalDist)
    assert isinstance(config.profession_net_worth["truncated"], TruncatedNormalDist)
