import random
from typing import Any, Dict

from world_builder import generate_chain_code
from world_builder.population_config import PopulationConfig
from world_builder.distributions_config import Distribution, sample_from_config

from namegen import generate_female_first_name, generate_male_first_name


class Character:
    def __init__(self, **attributes: Any):
        """
        Constructor for the character class, in which attributes are assigned dynamically
        via the passed-in dictionary.
        """
        # assign attributes dynamically by passing in a dict of attributes
        for name, value in attributes.items():
            setattr(self, name, value)

    def __repr__(self) -> str:
        """
        Returns the string representation of the Character.

        Example representation:
            Character(species='human', age=42).
        """
        props = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"Character({props})"


def _apply_factors(
    base_probs: Dict[str, float],
    category: str,
    sampled: Dict[str, Any],
    factors: Dict[str, Dict[str, Dict[str, Dict[str, float]]]],
) -> Dict[str, float]:
    """
    Apply factor multipliers for `category` based on previously sampled values.
    """
    adjusted = base_probs.copy()
    for dimension, key_map in factors.get(category, {}).items():
        value = sampled.get(dimension)
        if value is None:
            continue
        for subkey, mult in key_map.get(value, {}).items():
            if subkey in adjusted:
                adjusted[subkey] *= mult
    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: v / total for k, v in adjusted.items()}
    return adjusted


def create_character(config: PopulationConfig) -> Character:
    """
    Factory for Character. Samples discrete categories in the order specified
    by the 'factors' keys (respecting dependencies), then distributions,
    metadata, chain_code, and stub names.
    """
    sampled: Dict[str, Any] = {}

    # we sample first in the order of config.factors keys, then any remaining categories
    finite_categories = list(config.base_probabilities_finite.keys())
    order = []
    for cat in config.factors.keys():
        if cat in finite_categories:
            order.append(cat)
    for cat in finite_categories:
        if cat not in order:
            order.append(cat)

    for category in order:
        base_map = config.base_probabilities_finite[category]
        weights = _apply_factors(base_map, category, sampled, config.factors)
        choices, wts = zip(*weights.items())
        sampled[category] = random.choices(population=choices, weights=wts, k=1)[0]

    for category, dist in config.base_probabilities_distributions.items():
        if not isinstance(dist, Distribution):
            raise TypeError(f"Expected Distribution for '{category}', got {type(dist)}")
        sampled[category] = sample_from_config(dist)

    for field_name, field_value in config.metadata.items():
        sampled[field_name] = field_value

    species = sampled.get("species", "")
    is_female = str(sampled.get("gender", "")).lower() == "female"
    sampled["chain_code"] = generate_chain_code(species, is_female)

    if is_female:
        sampled["first_name"] = generate_female_first_name()
    else:
        sampled["first_name"] = generate_male_first_name()
    # TODO: replace stubs with real names after making a name generator
    sampled["surname"] = "Test"

    return Character(**sampled)
