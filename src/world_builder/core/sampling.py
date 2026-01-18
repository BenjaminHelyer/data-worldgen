"""
Generic sampling functions that work with any SamplingConfig.

These functions are domain-agnostic and can be used for population generation,
ecosystem modeling, or any other probabilistic sampling use case.
"""

import random
from typing import Any, Dict

from world_builder.distributions_config import Distribution, sample_from_config

from .config_protocol import SamplingConfig


def apply_factor_multipliers(
    base_probs: Dict[str, float],
    target_field: str,
    sampled_values: Dict[str, Any],
    all_factors: Dict[str, Dict[str, Dict[str, Dict[str, float]]]],
) -> Dict[str, float]:
    """
    Applies factor multipliers to adjust base probabilities.

    This is a generic function that works with any factor graph structure.
    It adjusts `base_probs` for `target_field` by walking:
      source_field -> target_field -> source_value -> {target_value: multiplier}

    Args:
        base_probs: Base probabilities for the target field
        target_field: The field being adjusted
        sampled_values: Already-sampled field values
        all_factors: The complete factor graph structure

    Returns:
        Adjusted probabilities (normalized to sum to 1.0)
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


def sample_finite_fields(
    config: SamplingConfig,
    sampled: Dict[str, Any],
) -> None:
    """
    Samples finite categorical fields in topological order.

    Mutates `sampled` by sampling each finite categorical field, respecting
    dependencies defined by the factor graph. Fields already present in `sampled`
    are skipped.

    Args:
        config: Configuration implementing SamplingConfig protocol
        sampled: Dictionary to populate with sampled values (modified in place)
    """
    finite_fields = list(config.base_probabilities_finite.keys())

    # sampling order: first any fields that appear as factor-targets, then the rest
    ordered = [field for field in config.factors if field in finite_fields]
    ordered += [field for field in finite_fields if field not in ordered]

    for field in ordered:
        if field in sampled:
            continue

        base_probs = config.base_probabilities_finite[field]
        adjusted = apply_factor_multipliers(
            base_probs=base_probs,
            target_field=field,
            sampled_values=sampled,
            all_factors=config.factors,
        )

        choices, weights = zip(*adjusted.items())
        sampled[field] = random.choices(choices, weights=weights, k=1)[0]


def sample_distribution_fields_with_overrides(
    config: SamplingConfig,
    sampled: Dict[str, Any],
) -> None:
    """
    Samples distribution-based fields with conditional overrides and transformations.

    Samples all fields defined in `base_probabilities_distributions`, applying:
    - The first matching override (from config.override_distributions), if any.
    - Then, applies any matching transformations from config.transform_distributions.

    Args:
        config: Configuration implementing SamplingConfig protocol
        sampled: Dictionary to populate with sampled values (modified in place)

    Raises:
        TypeError: If a distribution is not a valid Distribution instance
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
