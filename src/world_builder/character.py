import random
from typing import Any, Dict

from world_builder import generate_chain_code
from world_builder.population_config import PopulationConfig
from world_builder.distributions_config import Distribution, sample_from_config

from namegen import (
    generate_female_first_name,
    generate_male_first_name,
    generate_surname,
)


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
    target_field: str,
    sampled_values: Dict[str, Any],
    all_factors: Dict[str, Dict[str, Dict[str, Dict[str, float]]]],
) -> Dict[str, float]:
    """
    Adjusts the base probabilities for `target_field` using multipliers
    defined in `all_factors`, based on already sampled fields.

    This supports factor graphs of the form:
      source_field -> target_field -> source_value -> {target_value: multiplier}
    """
    adjusted = base_probs.copy()

    for source_field, target_map in all_factors.items():
        if target_field not in target_map:
            continue

        source_value = sampled_values.get(source_field)
        if source_value is None:
            continue

        multipliers = target_map[target_field].get(source_value, {})
        for target_value, multiplier in multipliers.items():
            if target_value in adjusted:
                adjusted[target_value] *= multiplier

    # Normalize the adjusted probabilities
    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: v / total for k, v in adjusted.items()}

    return adjusted


def _assign_metadata(sampled: Dict[str, Any], config: PopulationConfig) -> None:
    """
    Assigns constant metadata fields to the character.

    Metadata is an optional dictionary specified in the config, consisting of string key-value pairs.
    These fields are not sampled probabilistically; they are copied directly as constants into the character.
    Common use cases might include static identifiers like planet name, data version, or authoring info.

    Example:
        config.metadata = {"planet": "Tatooine", "author": "Obi-Wan"}
        ➞ sampled["planet"] = "Tatooine"
           sampled["author"] = "Obi-Wan"
    """
    for field_name, field_value in config.metadata.items():
        sampled[field_name] = field_value


def _assign_chain_code(sampled: Dict[str, Any]) -> None:
    """
    Generates and assigns a unique chain code to the character.

    The chain code is a UUIDv7-like identifier encoding species and gender information.
    It is useful for later tracing or decoding metadata about the character.

    Format (example):
        "CC-HUM-M-0196940f-92d3-7000-97b8-f3f9cf01b7f3"

    Components:
        - "CC" prefix
        - Species abbreviation (e.g., "HUM" for human, "ROD" for rodian)
        - Gender abbreviation ("M" or "F")
        - A UUIDv7-like suffix that encodes time-based uniqueness

    The species and gender are pulled from the sampled fields. If missing, defaults are blank.
    """
    species = sampled.get("species", "")
    is_female = str(sampled.get("gender", "")).lower() == "female"
    sampled["chain_code"] = generate_chain_code(species, is_female)


def _assign_names(sampled: Dict[str, Any]) -> None:
    """
    Generates and assigns a first name and surname for the character.

    Name generation is performed using a generative model (e.g., a Markov chain),
    trained separately for male and female first names, and for surnames by species.

    Details:
        - First name is generated using either `generate_female_first_name()` or
          `generate_male_first_name()` based on the gender field.
        - Surname is generated using `generate_surname(species=...)`, allowing species-specific naming patterns.

    These generative functions ensure name plausibility while allowing creative variation.

    Example output:
        - first_name: "Sa" (generated for female)
        - surname: "Saokaell" (generated for a human)
    """
    species = sampled.get("species", "")
    is_female = str(sampled.get("gender", "")).lower() == "female"
    sampled["first_name"] = (
        generate_female_first_name() if is_female else generate_male_first_name()
    )
    sampled["surname"] = generate_surname(species=species)


def _sample_finite_fields(config: PopulationConfig) -> Dict[str, Any]:
    """
    Samples values for all finite categorical fields using base probabilities and
    modifying them based on conditional factors from previously sampled fields.

    The sampling respects the topological order of `factors` to enable causal consistency.
    """
    sampled: Dict[str, Any] = {}

    finite_fields = list(config.base_probabilities_finite.keys())

    # determine the sampling order: first factor targets, then independent fields
    ordered_fields = [field for field in config.factors if field in finite_fields]
    ordered_fields += [field for field in finite_fields if field not in ordered_fields]

    for field in ordered_fields:
        base_probs = config.base_probabilities_finite[field]

        # adjust base_probs if the field is influenced by other sampled fields
        adjusted_probs = _apply_factors(
            base_probs=base_probs,
            target_field=field,
            sampled_values=sampled,
            all_factors=config.factors
        )

        # sample one value based on adjusted probabilities
        options, weights = zip(*adjusted_probs.items())
        sampled[field] = random.choices(population=options, weights=weights, k=1)[0]

    return sampled


def _sample_distribution_fields_with_overrides(
    config: PopulationConfig, sampled: Dict[str, Any]
) -> None:
    """
    Samples all fields defined in `base_probabilities_distributions`, applying conditional
    overrides if applicable.

    Behavior:
    - For each distributional field (e.g., "age"), use the base distribution by default.
    - If any overrides are defined in `config.override_distributions`, evaluate them **in order**.
    - The **first matching override** (based on sampled field values) is used to replace the base distribution.
    - If no override matches, fall back to the original base distribution.

    A match occurs when:
    - The override's `field` matches the current category, AND
    - All key-value pairs in the override's `condition` match what's already sampled.

    Example:
        If category = "age" and sampled = {"profession": "soldier"},
        and override.condition = {"profession": "soldier"},
        then override.distribution replaces base_distributions["age"].

    This function modifies the `sampled` dict in-place.
    """
    for category, base_dist in config.base_probabilities_distributions.items():
        final_dist = base_dist  # Default to base distribution

        if config.override_distributions:
            for override in config.override_distributions:
                if override.field != category:
                    continue
                if all(sampled.get(k) == v for k, v in override.condition.items()):
                    final_dist = override.distribution
                    break  # First match wins

        if not isinstance(final_dist, Distribution):
            raise TypeError(
                f"Expected Distribution for '{category}', got {type(final_dist)}"
            )

        sampled[category] = sample_from_config(final_dist)


def create_character(config: PopulationConfig) -> Character:
    """
    Factory for Character. Samples discrete categories in the order specified
    by the 'factors' keys (respecting dependencies), then applies distribution-based
    sampling with optional conditional overrides, and fills metadata + names.
    """
    sampled: Dict[str, Any] = {}

    sampled.update(_sample_finite_fields(config))
    _sample_distribution_fields_with_overrides(config, sampled)
    _assign_chain_code(sampled)
    _assign_names(sampled)
    _assign_metadata(sampled, config)

    return Character(**sampled)
