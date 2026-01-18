from pathlib import Path

import pytest
from pydantic import ValidationError

from world_builder.population.config import load_config, PopulationConfig
from world_builder.distributions_config import (
    Distribution,
    DistributionTransformOperation,
    NormalDist,
)

parent_dir = Path(__file__).resolve().parent
CONFIG_DIR = parent_dir / "config"
CONFIG_FILE = CONFIG_DIR / "wb_config_micro.json"


@pytest.mark.parametrize(
    "filename",
    [
        "wb_config_micro.json",
        "wb_config_small.json",
        "wb_config_medium.json",
        "wb_config_large.json",
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
        "metadata": {"planet": "Tatooine"},
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
        "metadata": {"planet": "Tatooine"},
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
        "metadata": {"planet": "Tatooine"},
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
        "metadata": {"planet": "Tatooine"},
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
        "metadata": {"planet": "Tatooine"},
    },
    # factors list unknown fields -- in this case, field names
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
        "factors": {"town": {"allegiance": {"Mos Eisley": {"Rebel": 5.0}}}},
        "metadata": {"planet": "Tatooine"},
    },
    # factors list unknown fields -- in this case, field values
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
        "factors": {"city": {"allegiance": {"Mos Taike": {"Rebel": 5.0}}}},
        "metadata": {"planet": "Tatooine"},
    },
    # factor graph has a cycle -- which will break ancestral sampling
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
        "factors": {
            "city": {"allegiance": {"Mos Eisley": {"Rebel": 5.0}}},
            "allegiance": {"city": {"Rebel": {"Mos Eisley": 2.0}}},
        },
        "metadata": {"planet": "Tatooine"},
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
    assert config.metadata["planet"] == "Tatooine"


@pytest.mark.parametrize("config_data", bad_configs)
def test_populationconfig_invalid(config_data):
    """
    Invalid PopulationConfig data should raise a ValidationError.
    """
    with pytest.raises(ValidationError):
        PopulationConfig(**config_data)


@pytest.mark.parametrize(
    "config_json",
    [
        # Case 1: Profession -> Age override
        {
            "base_probabilities_finite": {"profession": {"soldier": 1.0}},
            "base_probabilities_distributions": {
                "age": {"type": "normal", "mean": 30, "std": 10}
            },
            "override_distributions": [
                {
                    "condition": {"profession": "soldier"},
                    "field": "age",
                    "distribution": {"type": "normal", "mean": 3.0, "std": 0.5},
                }
            ],
        },
        # Case 2: Allegiance -> Age override
        {
            "base_probabilities_finite": {
                "allegiance": {"Imperial": 0.6, "Rebel": 0.4}
            },
            "base_probabilities_distributions": {
                "age": {"type": "normal", "mean": 25, "std": 5}
            },
            "override_distributions": [
                {
                    "condition": {"allegiance": "Imperial"},
                    "field": "age",
                    "distribution": {"type": "normal", "mean": 250, "std": 0.1},
                }
            ],
        },
    ],
)
def test_valid_override_distributions(config_json):
    config = PopulationConfig(**config_json)
    assert config.override_distributions is not None


@pytest.mark.parametrize(
    "config_json",
    [
        # Case 1: Invalid condition key 'species'
        {
            "base_probabilities_finite": {"profession": {"soldier": 1.0}},
            "base_probabilities_distributions": {
                "age": {"type": "normal", "mean": 30, "std": 10}
            },
            "override_distributions": [
                {
                    "condition": {"species": "wookiee"},
                    "field": "age",
                    "distribution": {"type": "lognormal", "mean": 3.0, "sigma": 0.5},
                }
            ],
        },
        # Case 2: Invalid override target field 'height' not in distributions
        {
            "base_probabilities_finite": {"profession": {"pilot": 1.0}},
            "base_probabilities_distributions": {
                "age": {"type": "normal", "mean": 30, "std": 10}
            },
            "override_distributions": [
                {
                    "condition": {"profession": "pilot"},
                    "field": "height",  # <-- invalid field
                    "distribution": {"type": "normal", "mean": 1.75, "std": 0.1},
                }
            ],
        },
    ],
)
def test_invalid_override_distributions(config_json):
    with pytest.raises(ValidationError) as exc_info:
        PopulationConfig(**config_json)
    assert "override" in str(exc_info.value).lower()


@pytest.mark.parametrize(
    "transform_distributions",
    [
        # Only mean shift
        {
            "age": {
                "species": {"Wookiee": DistributionTransformOperation(mean_shift=100.0)}
            }
        },
        # Only std multiplier
        {"age": {"city": {"Mos Eisley": DistributionTransformOperation(std_mult=2.0)}}},
        # Both mean shift and std multiplier
        {
            "age": {
                "city": {
                    "Mos Eisley": DistributionTransformOperation(
                        mean_shift=-5.0, std_mult=1.5
                    )
                },
                "species": {"Human": DistributionTransformOperation(mean_shift=2.0)},
            }
        },
        # Empty transform (permitted now)
        {"age": {"species": {"Rodian": DistributionTransformOperation()}}},
    ],
)
def test_valid_transform_distributions(transform_distributions):
    config = PopulationConfig(
        base_probabilities_finite={},
        base_probabilities_distributions={
            "age": NormalDist(type="normal", mean=30, std=5)
        },
        factors={},
        override_distributions=[],
        transform_distributions=transform_distributions,
        metadata={},
    )
    assert config.transform_distributions == transform_distributions


@pytest.mark.parametrize(
    "transform_distributions",
    [
        # std_mult is negative
        {
            "age": {
                "city": {"Mos Eisley": DistributionTransformOperation(std_mult=-1.0)}
            }
        },
        # std_mult is zero
        {"age": {"city": {"Mos Eisley": DistributionTransformOperation(std_mult=0.0)}}},
        # mean_shift is NaN
        {
            "age": {
                "species": {
                    "Wookiee": DistributionTransformOperation(mean_shift=float("nan"))
                }
            }
        },
        # std_mult is infinity
        {
            "age": {
                "species": {
                    "Wookiee": DistributionTransformOperation(std_mult=float("inf"))
                }
            }
        },
    ],
)
def test_invalid_transform_distributions(transform_distributions):
    with pytest.raises(ValidationError):
        PopulationConfig(
            base_probabilities_finite={},
            base_probabilities_distributions={
                "age": NormalDist(type="normal", mean=30, std=5)
            },
            factors={},
            override_distributions=[],
            transform_distributions=transform_distributions,
            metadata={},
        )
