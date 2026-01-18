from pathlib import Path

import pytest
from pydantic import ValidationError

from world_builder.ecosystem.config import load_config, EcosystemConfig
from world_builder.distributions_config import (
    Distribution,
    DistributionTransformOperation,
    NormalDist,
)

parent_dir = Path(__file__).resolve().parent
CONFIG_DIR = parent_dir / "config"


@pytest.mark.parametrize(
    "filename",
    [
        "ecosystem_config_micro.json",
    ],
)
def test_load_config_smoke(filename):
    """
    Smoke test: ensure that loading a known good config file works without errors.
    """
    config_path = CONFIG_DIR / filename
    if not config_path.exists():
        pytest.skip(f"Config file {filename} does not exist")
    config = load_config(config_path)
    assert config is not None


# Valid configurations should use the new schema keys:
good_configs = [
    # test for data without factors
    {
        "base_probabilities_finite": {
            "habitat": {"forest": 1.0},
            "species": {"fox": 1.0},
            "trophic_level": {"carnivore": 1.0},
        },
        "base_probabilities_distributions": {
            "age": {"type": "truncated_normal", "mean": 5, "std": 2, "lower": 0}
        },
        "metadata": {"ecosystem": "Test Reserve"},
    },
    # test for data with factors
    {
        "base_probabilities_finite": {
            "habitat": {"forest": 1.0},
            "species": {"fox": 1.0},
            "trophic_level": {"carnivore": 1.0},
        },
        "base_probabilities_distributions": {
            "age": {"type": "truncated_normal", "mean": 5, "std": 2, "lower": 0}
        },
        "factors": {"habitat": {"species": {"forest": {"fox": 2.0}}}},
        "metadata": {"ecosystem": "Test Reserve"},
    },
]

# Invalid configurations should trigger validation errors:
bad_configs = [
    # probabilities don't sum to 1.0
    {
        "base_probabilities_finite": {
            "species": {"fox": 0.5, "rabbit": 0.3}  # sums to 0.8, not 1.0
        },
        "base_probabilities_distributions": {},
    },
    # negative factor
    {
        "base_probabilities_finite": {
            "habitat": {"forest": 1.0},
            "species": {"fox": 1.0},
        },
        "base_probabilities_distributions": {},
        "factors": {"habitat": {"species": {"forest": {"fox": -1.0}}}},
    },
    # factor references non-existent field
    {
        "base_probabilities_finite": {
            "species": {"fox": 1.0},
        },
        "base_probabilities_distributions": {},
        "factors": {
            "biome": {"species": {"tundra": {"fox": 2.0}}}
        },  # biome not defined
    },
]


@pytest.mark.parametrize("config_data", good_configs)
def test_ecosystemconfig_valid(config_data):
    """
    Valid EcosystemConfig data should instantiate without errors,
    and retain the correct structure.
    """
    config = EcosystemConfig(**config_data)
    # finite probabilities
    assert config.base_probabilities_finite == config_data["base_probabilities_finite"]
    # distributions loaded as Distribution instances
    assert set(config.base_probabilities_distributions.keys()) == set(
        config_data["base_probabilities_distributions"].keys()
    )
    for key, dist in config.base_probabilities_distributions.items():
        assert isinstance(dist, Distribution)
    if "metadata" in config_data and "ecosystem" in config_data["metadata"]:
        assert config.metadata["ecosystem"] == config_data["metadata"]["ecosystem"]


@pytest.mark.parametrize("config_data", bad_configs)
def test_ecosystemconfig_invalid(config_data):
    """
    Invalid EcosystemConfig data should raise a ValidationError.
    """
    with pytest.raises(ValidationError):
        EcosystemConfig(**config_data)


@pytest.mark.parametrize(
    "config_json",
    [
        # Case 1: Species -> Age override
        {
            "base_probabilities_finite": {"species": {"fox": 1.0}},
            "base_probabilities_distributions": {
                "age": {"type": "truncated_normal", "mean": 5, "std": 2, "lower": 0}
            },
            "override_distributions": [
                {
                    "condition": {"species": "fox"},
                    "field": "age",
                    "distribution": {
                        "type": "truncated_normal",
                        "mean": 3.0,
                        "std": 0.5,
                        "lower": 0,
                    },
                }
            ],
        },
        # Case 2: Habitat -> Population size override
        {
            "base_probabilities_finite": {"habitat": {"forest": 0.6, "grassland": 0.4}},
            "base_probabilities_distributions": {
                "age": {"type": "truncated_normal", "mean": 5, "std": 2, "lower": 0}
            },
            "override_distributions": [
                {
                    "condition": {"habitat": "forest"},
                    "field": "age",
                    "distribution": {
                        "type": "truncated_normal",
                        "mean": 7,
                        "std": 2,
                        "lower": 0,
                    },
                }
            ],
        },
    ],
)
def test_valid_override_distributions(config_json):
    config = EcosystemConfig(**config_json)
    assert config.override_distributions is not None


@pytest.mark.parametrize(
    "config_json",
    [
        # Case 1: Invalid condition key 'biome'
        {
            "base_probabilities_finite": {"species": {"fox": 1.0}},
            "base_probabilities_distributions": {
                "age": {"type": "truncated_normal", "mean": 5, "std": 2, "lower": 0}
            },
            "override_distributions": [
                {
                    "condition": {"biome": "tundra"},
                    "field": "age",
                    "distribution": {
                        "type": "truncated_normal",
                        "mean": 3.0,
                        "std": 0.5,
                        "lower": 0,
                    },
                }
            ],
        },
        # Case 2: Invalid override target field 'height' not in distributions
        {
            "base_probabilities_finite": {"species": {"fox": 1.0}},
            "base_probabilities_distributions": {
                "age": {"type": "normal", "mean": 5, "std": 2}
            },
            "override_distributions": [
                {
                    "condition": {"species": "fox"},
                    "field": "height",  # <-- invalid field
                    "distribution": {"type": "normal", "mean": 1.0, "std": 0.1},
                }
            ],
        },
    ],
)
def test_invalid_override_distributions(config_json):
    with pytest.raises(ValidationError):
        EcosystemConfig(**config_json)
