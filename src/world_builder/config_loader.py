import json

from .exceptions import ProbabilityError


def load_config(config_filepath):
    """
    Loads the JSON configuration file and validates each distribution.
    """
    with open(config_filepath, "r") as f:
        config = json.load(f)
    validate_config(config)
    return config


def validate_config(config):
    """
    Validates that each distribution in the config sums to 1.
    Expected distribution keys: species_weights, gender_weights, allegiance_weights, profession_weights, city_weights.
    Raises ProbabilityError if a distribution is invalid.
    """
    distribution_keys = [
        "species_weights",
        "gender_weights",
        "allegiance_weights",
        "profession_weights",
        "city_weights",
    ]
    for key in distribution_keys:
        if key in config:
            total = sum(config[key].values())
            # Allow for floating point imprecision
            if abs(total - 1.0) > 1e-6:
                raise ProbabilityError(
                    f"Invalid probability distribution for '{key}': sum = {total}, expected 1.0."
                )
