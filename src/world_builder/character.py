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


def _sample_finite_fields(
    config: PopulationConfig,
    sampled: Dict[str, Any],
) -> None:
    """
    Mutates `sampled` by sampling each finite categorical field in topological order
    (respecting config.factors). Any field already present in `sampled` is skipped.
    """
    finite_fields = list(config.base_probabilities_finite.keys())

    # sampling order: first any fields that appear as factor-targets, then the rest
    ordered = [field for field in config.factors if field in finite_fields]
    ordered += [field for field in finite_fields if field not in ordered]

    for field in ordered:
        if field in sampled:
            continue

        base_probs = config.base_probabilities_finite[field]
        adjusted = _apply_factor_multipliers(
            base_probs=base_probs,
            target_field=field,
            sampled_values=sampled,
            all_factors=config.factors,
        )

        choices, weights = zip(*adjusted.items())
        sampled[field] = random.choices(choices, weights=weights, k=1)[0]


def _apply_factor_multipliers(
    base_probs: Dict[str, float],
    target_field: str,
    sampled_values: Dict[str, Any],
    all_factors: Dict[str, Dict[str, Dict[str, Dict[str, float]]]],
) -> Dict[str, float]:
    """
    Applies the factor multipliers.

    Adjust `base_probs` for `target_field` by walking:
      source_field -> target_field -> source_value -> {target_value: multiplier}
    """
    adjusted = base_probs.copy()

    for source_field, target_map in all_factors.items():
        # only if this source field actually influences our target
        if target_field not in target_map:
            continue

        source_val = sampled_values.get(source_field)
        if source_val is None:
            continue

        for t_val, mult in target_map[target_field].get(source_val, {}).items():
            if t_val in adjusted:
                adjusted[t_val] *= mult

    total = sum(adjusted.values())
    if total > 0:
        for k in adjusted:
            adjusted[k] /= total

    return adjusted


def _sample_distribution_fields_with_overrides(
    config: PopulationConfig, sampled: Dict[str, Any]
) -> None:
    """
    Samples all fields defined in `base_probabilities_distributions`, applying:
    - The first matching override (from config.override_distributions), if any.
    - Then, applies any matching transformations from config.transform_distributions.

    Sampling logic:
    1. Start with the base distribution.
    2. If any overrides match the already-sampled fields, apply the first one.
    3. Apply any applicable distribution transformations using sampled fields.
    4. Sample from the resulting distribution and store in the `sampled` dict.
    """
    for category, base_dist in config.base_probabilities_distributions.items():
        final_dist = base_dist  # start with base distribution

        if config.override_distributions:
            for override in config.override_distributions:
                if override.field != category:
                    continue
                if all(sampled.get(k) == v for k, v in override.condition.items()):
                    final_dist = override.distribution
                    break  # first match wins

        if category in config.transform_distributions:
            trait_map = config.transform_distributions[category]
            for trait_field, value_map in trait_map.items():
                trait_value = sampled.get(trait_field)
                if trait_value is None or trait_value not in value_map:
                    continue
                transform = value_map[trait_value]
                final_dist = final_dist.with_transform(transform)

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

    _sample_finite_fields(config, sampled)
    _sample_distribution_fields_with_overrides(config, sampled)
    _assign_chain_code(sampled)
    _assign_names(sampled)
    _assign_metadata(sampled, config)

    return Character(**sampled)
