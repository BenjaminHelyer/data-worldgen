import random
from typing import Any, Dict

from .chain_code import generate_chain_code
from world_builder.population_config import PopulationConfig
from world_builder.distributions_config import Distribution, sample_from_config


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
    Apply any factor multipliers for `category` based on previously sampled values.
    - factors structure: factor_name -> dimension_name -> key -> subkey -> multiplier
    """
    adjusted = base_probs.copy()
    # look up only the entries that affect this category
    for dimension, key_map in factors.get(category, {}).items():
        value = sampled.get(dimension)
        if value is None:
            continue
        # multipliers for this specific dimension=value
        for subkey, mult in key_map.get(value, {}).items():
            if subkey in adjusted:
                adjusted[subkey] *= mult
    # re-normalize to sum to 1 (if there's any weight left)
    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: v / total for k, v in adjusted.items()}
    return adjusted


def create_character(config: PopulationConfig) -> Character:
    """
    Factory function for the Character class.

    Samples *all* finite categories, then *all* distribution categories,
    then adds planet, generates a chain_code, and stubs names.
    Factors in config.factors will be applied automatically to each finite category.
    """
    sampled: Dict[str, Any] = {}

    # sample every discrete category in the config
    for category, base_map in config.base_probabilities_finite.items():
        # apply any relevant factors
        weights = _apply_factors(base_map, category, sampled, config.factors)
        choices, wts = zip(*weights.items())
        sampled[category] = random.choices(population=choices, weights=wts, k=1)[0]

    # sample every distribution category
    for category, dist in config.base_probabilities_distributions.items():
        if not isinstance(dist, Distribution):
            raise TypeError(f"Expected Distribution for '{category}', got {type(dist)}")
        sampled[category] = sample_from_config(dist)

    # sample metadata fields
    for field_name, field_value in config.metadata.items():
        sampled[field_name] = field_value

    # generate chain code (requires a 'species' and 'gender' entry)
    species = sampled.get("species", "")
    is_female = str(sampled.get("gender", "")).lower() == "female"
    sampled["chain_code"] = generate_chain_code(species, is_female)

    # 5) stubbed name logic (swap in your real generator here)
    sampled["first_name"] = "Test"
    sampled["surname"] = "Test"

    return Character(**sampled)
