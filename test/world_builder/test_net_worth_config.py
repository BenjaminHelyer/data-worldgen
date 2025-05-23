"""
Tests for the net worth configuration module.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from world_builder.net_worth_config import load_config, NetWorthConfig
from world_builder.distributions_config import (
    Distribution,
    NormalDist,
    LogNormalDist,
    TruncatedNormalDist,
    FunctionBasedDist,
    FunctionConfig,
    NoiseFunctionConfig,
)

parent_dir = Path(__file__).resolve().parent
CONFIG_DIR = parent_dir / "config"
CONFIG_FILE = CONFIG_DIR / "nw_config_micro.json"


@pytest.mark.parametrize(
    "filename",
    [
        "nw_config_micro.json",
        "nw_config_large.json",
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
    # test for basic function-based distribution
    {
        "profession_liquid_currency": {
            "farmer": {
                "field_name": "age",
                "mean_function": {
                    "type": "linear",
                    "params": {"slope": 5, "intercept": 100},
                },
                "noise_function": {
                    "type": "normal",
                    "params": {
                        "field_name": "age",
                        "scale_factor": {
                            "type": "linear",
                            "params": {"slope": 0.1, "intercept": 0},
                        },
                    },
                },
            }
        },
        "metadata": {"currency": "credits", "era": "Clone Wars"},
    },
    # test for multiple professions with different functions
    {
        "profession_liquid_currency": {
            "merchant": {
                "field_name": "experience",
                "mean_function": {
                    "type": "exponential",
                    "params": {"base": 50, "rate": 0.1},
                },
                "noise_function": {
                    "type": "normal",
                    "params": {
                        "field_name": "experience",
                        "scale_factor": {
                            "type": "quadratic",
                            "params": {"a": 0.01, "b": 0, "c": 0},
                        },
                    },
                },
            }
        },
        "metadata": {"currency": "credits"},
    },
]

# Invalid configurations should trigger validation errors:
bad_configs = [
    # missing field_name
    {
        "profession_liquid_currency": {
            "farmer": {
                "mean_function": {
                    "type": "linear",
                    "params": {"slope": 5, "intercept": 100},
                },
                "noise_function": {
                    "type": "normal",
                    "params": {
                        "field_name": "age",
                        "scale_factor": {
                            "type": "linear",
                            "params": {"slope": 0.1, "intercept": 0},
                        },
                    },
                },
            }
        },
        "metadata": {"currency": "credits"},
    },
    # invalid function type
    {
        "profession_liquid_currency": {
            "farmer": {
                "field_name": "age",
                "mean_function": {
                    "type": "invalid",
                    "params": {"slope": 5, "intercept": 100},
                },
                "noise_function": {
                    "type": "normal",
                    "params": {
                        "field_name": "age",
                        "scale_factor": {
                            "type": "linear",
                            "params": {"slope": 0.1, "intercept": 0},
                        },
                    },
                },
            }
        },
        "metadata": {"currency": "credits"},
    },
    # missing required function parameters
    {
        "profession_liquid_currency": {
            "farmer": {
                "field_name": "age",
                "mean_function": {
                    "type": "linear",
                    "params": {"slope": 5},  # missing intercept
                },
                "noise_function": {
                    "type": "normal",
                    "params": {
                        "field_name": "age",
                        "scale_factor": {
                            "type": "linear",
                            "params": {"slope": 0.1, "intercept": 0},
                        },
                    },
                },
            }
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
    assert set(config.profession_liquid_currency.keys()) == set(
        config_data["profession_liquid_currency"].keys()
    )
    for profession, dist in config.profession_liquid_currency.items():
        assert isinstance(dist, FunctionBasedDist)
        # Validate the structure of the function-based distribution
        assert isinstance(dist.mean_function, FunctionConfig)
        assert isinstance(dist.noise_function, NoiseFunctionConfig)
        assert dist.field_name is not None
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


def test_function_types():
    """
    Test that different function types are properly handled.
    """
    config = NetWorthConfig(
        profession_liquid_currency={
            "linear_test": {
                "field_name": "age",
                "mean_function": {
                    "type": "linear",
                    "params": {"slope": 5, "intercept": 100},
                },
                "noise_function": {
                    "type": "normal",
                    "params": {
                        "field_name": "age",
                        "scale_factor": {
                            "type": "linear",
                            "params": {"slope": 0.1, "intercept": 0},
                        },
                    },
                },
            },
            "exponential_test": {
                "field_name": "experience",
                "mean_function": {
                    "type": "exponential",
                    "params": {"base": 50, "rate": 0.1},
                },
                "noise_function": {
                    "type": "normal",
                    "params": {
                        "field_name": "experience",
                        "scale_factor": {
                            "type": "quadratic",
                            "params": {"a": 0.01, "b": 0, "c": 0},
                        },
                    },
                },
            },
        },
        metadata={"test": "test"},
    )

    for profession, dist in config.profession_liquid_currency.items():
        assert isinstance(dist, FunctionBasedDist)
        assert dist.field_name is not None
        assert isinstance(dist.mean_function, FunctionConfig)
        assert isinstance(dist.noise_function, NoiseFunctionConfig)


def test_load_large_config():
    """
    Test loading and validating the large config file specifically.
    This test verifies the structure and content of the large config file.
    """
    config_path = CONFIG_DIR / "nw_config_large.json"
    config = load_config(config_path)

    # Test basic structure
    assert isinstance(config, NetWorthConfig)
    assert hasattr(config, "profession_liquid_currency")
    assert hasattr(config, "metadata")

    # Test metadata
    assert config.metadata["currency"] == "credits"
    assert config.metadata["era"] == "Clone Wars"

    # Test specific professions with their expected configurations
    profession_configs = {
        "bounty hunter": {"noise_type": "normal", "mean_type": "exponential"},
        "Jedi": {"noise_type": "normal", "mean_type": "constant"},
        "politician": {"noise_type": "lognormal", "mean_type": "linear"},
        "wealthy": {"noise_type": "truncated_normal", "mean_type": "exponential"},
    }

    for profession, expected_config in profession_configs.items():
        assert profession in config.profession_liquid_currency
        dist = config.profession_liquid_currency[profession]

        # Verify distribution structure
        assert isinstance(dist, FunctionBasedDist)
        assert dist.field_name == "age"
        assert isinstance(dist.mean_function, FunctionConfig)
        assert isinstance(dist.noise_function, NoiseFunctionConfig)

        # Verify function types match expected configuration
        assert dist.noise_function.type == expected_config["noise_type"]
        assert dist.mean_function.type == expected_config["mean_type"]

        # Verify required parameters exist
        assert "field_name" in dist.noise_function.params
        assert "scale_factor" in dist.noise_function.params


def test_load_config_with_primary_residence():
    """
    Test loading a config file that includes the optional primary residence fields.
    """
    config_path = CONFIG_DIR / "nw_config_small.json"
    config = load_config(config_path)

    # Test basic structure
    assert isinstance(config, NetWorthConfig)
    assert config.profession_has is not None
    assert config.profession_value is not None
    assert "primary_residence" in config.profession_has
    assert "primary_residence" in config.profession_value
    assert "farmer" in config.profession_has["primary_residence"]
    assert "farmer" in config.profession_value["primary_residence"]

    # Test residence ownership config structure
    residence_config = config.profession_has["primary_residence"]["farmer"]
    assert residence_config.field_name == "age"
    assert residence_config.mean_function.type == "linear"
    assert residence_config.mean_function.params.slope == 0.02
    assert residence_config.mean_function.params.intercept == 0.1

    # Test residence value config structure
    value_config = config.profession_value["primary_residence"]["farmer"]
    assert value_config.field_name == "age"
    assert value_config.mean_function.type == "linear"
    assert value_config.mean_function.params.slope == 1000
    assert value_config.mean_function.params.intercept == 50000
    assert value_config.noise_function.type == "normal"
    assert value_config.noise_function.params["scale_factor"].type == "linear"
    assert value_config.noise_function.params["scale_factor"].params.slope == 100
    assert value_config.noise_function.params["scale_factor"].params.intercept == 5000


def test_load_config_with_all_assets():
    """
    Test loading a config file that includes all the optional asset fields.
    """
    config_path = CONFIG_DIR / "nw_config_small.json"
    config = load_config(config_path)

    # Test basic structure
    assert isinstance(config, NetWorthConfig)
    assert config.profession_has is not None
    assert config.profession_value is not None

    # Test that each asset type exists in both has and value configs
    asset_types = [
        "primary_residence",
        "other_properties",
        "starships",
        "speeders",
        "other_vehicles",
        "luxury_property",
        "galactic_stock",
        "business",
    ]

    for asset_type in asset_types:
        assert asset_type in config.profession_has
        assert asset_type in config.profession_value
        assert "farmer" in config.profession_has[asset_type]
        assert "farmer" in config.profession_value[asset_type]

    # Test that each asset type has the correct structure for "farmer" profession
    asset_configs = [
        (
            "primary_residence",
            0.02,
            0.1,
            1000,
            50000,
            100,
            5000,
        ),  # ownership_slope, ownership_intercept, value_slope, value_intercept, noise_slope, noise_intercept
        (
            "other_properties",
            0.01,
            0.05,
            500,
            25000,
            50,
            2500,
        ),
        (
            "starships",
            0.005,
            0.01,
            2000,
            100000,
            200,
            10000,
        ),
        (
            "speeders",
            0.015,
            0.05,
            300,
            15000,
            30,
            1500,
        ),
        (
            "other_vehicles",
            0.01,
            0.03,
            400,
            20000,
            40,
            2000,
        ),
        (
            "luxury_property",
            0.008,
            0.02,
            3000,
            150000,
            300,
            15000,
        ),
        (
            "galactic_stock",
            0.012,
            0.04,
            800,
            40000,
            80,
            4000,
        ),
        (
            "business",
            0.01,
            0.03,
            2500,
            125000,
            250,
            12500,
        ),
    ]

    for (
        asset_type,
        ownership_slope,
        ownership_intercept,
        value_slope,
        value_intercept,
        noise_slope,
        noise_intercept,
    ) in asset_configs:
        # Test ownership config
        has_config = config.profession_has[asset_type]["farmer"]
        assert has_config.field_name == "age"
        assert has_config.mean_function.type == "linear"
        assert has_config.mean_function.params.slope == ownership_slope
        assert has_config.mean_function.params.intercept == ownership_intercept

        # Test value config
        value_config = config.profession_value[asset_type]["farmer"]
        assert value_config.field_name == "age"
        assert value_config.mean_function.type == "linear"
        assert value_config.mean_function.params.slope == value_slope
        assert value_config.mean_function.params.intercept == value_intercept
        assert value_config.noise_function.type == "normal"
        assert value_config.noise_function.params["scale_factor"].type == "linear"
        assert (
            value_config.noise_function.params["scale_factor"].params.slope
            == noise_slope
        )
        assert (
            value_config.noise_function.params["scale_factor"].params.intercept
            == noise_intercept
        )
