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
        "profession_net_worth": {
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
        "profession_net_worth": {
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
        "profession_net_worth": {
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
        "profession_net_worth": {
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
        "profession_net_worth": {
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
    assert set(config.profession_net_worth.keys()) == set(
        config_data["profession_net_worth"].keys()
    )
    for profession, dist in config.profession_net_worth.items():
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
        profession_net_worth={
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

    for profession, dist in config.profession_net_worth.items():
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
    assert hasattr(config, "profession_net_worth")
    assert hasattr(config, "metadata")
    
    # Test metadata
    assert config.metadata["currency"] == "credits"
    assert config.metadata["era"] == "Clone Wars"
    
    # Test specific professions with their expected configurations
    profession_configs = {
        "bounty hunter": {
            "noise_type": "normal",
            "mean_type": "exponential"
        },
        "Jedi": {
            "noise_type": "normal",
            "mean_type": "constant"
        },
        "politician": {
            "noise_type": "lognormal",
            "mean_type": "linear"
        },
        "wealthy": {
            "noise_type": "truncated_normal",
            "mean_type": "exponential"
        }
    }
    
    for profession, expected_config in profession_configs.items():
        assert profession in config.profession_net_worth
        dist = config.profession_net_worth[profession]
        
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
