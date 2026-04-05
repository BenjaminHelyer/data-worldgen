"""
Generic sampling functions that work with any SamplingConfig.

These functions are domain-agnostic and can be used for population generation,
ecosystem modeling, or any other probabilistic sampling use case.
"""

from __future__ import annotations

import weakref
from typing import Any, Dict, List

import numpy as np
from scipy.stats import truncnorm

from world_builder.distributions_config import (
    BernoulliBasedDist,
    Distribution,
    FunctionBasedDist,
    LogNormalDist,
    NormalDist,
    TruncatedNormalDist,
    is_distribution,
    _sample,
)

from .config_protocol import SamplingConfig
from .finite_pmf import FiniteSamplingTables, build_finite_sampling_tables

_tables_by_id: Dict[int, tuple[weakref.ref, FiniteSamplingTables]] = {}


def _get_cached_finite_tables(config: SamplingConfig) -> FiniteSamplingTables:
    i = id(config)
    entry = _tables_by_id.get(i)
    if entry is not None:
        wr, tables = entry
        if wr() is config:
            return tables
        _tables_by_id.pop(i, None)

    tables = build_finite_sampling_tables(config)
    try:
        wr = weakref.ref(
            config, lambda _r, _i=i: _tables_by_id.pop(_i, None)
        )
    except TypeError:
        return tables

    _tables_by_id[i] = (wr, tables)
    return tables


def get_finite_sampling_tables(config: SamplingConfig) -> FiniteSamplingTables:
    """
    Return precomputed conditional PMF tables for finite fields.

    Tables are built on first use and cached for the lifetime of ``config``.
    """
    return _get_cached_finite_tables(config)


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
    tables = _get_cached_finite_tables(config)
    rng = np.random.default_rng()

    for field in tables.ordered_finite_fields:
        if field in sampled:
            continue

        parents = tables.parent_fields[field]
        for p in parents:
            if p not in sampled:
                raise KeyError(
                    f"Cannot sample finite field {field!r}: parent {p!r} is missing from sampled."
                )

        if parents:
            idx = tuple(tables.category_to_index[p][sampled[p]] for p in parents)
            pmf = tables.conditional_pmfs[field][idx]
        else:
            pmf = tables.conditional_pmfs[field]

        cum = np.cumsum(pmf)
        if cum.size:
            cum[-1] = 1.0
        u = float(rng.random())
        j = int(np.searchsorted(cum, u, side="right"))
        if j >= len(cum):
            j = len(cum) - 1
        sampled[field] = tables.categories[field][j]


def sample_finite_fields_batch(
    config: SamplingConfig,
    n: int,
    rng: np.random.Generator,
) -> Dict[str, np.ndarray]:
    """
    Sample all finite fields for n characters; returns int32 index arrays per field.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    tables = _get_cached_finite_tables(config)
    out: Dict[str, np.ndarray] = {}

    for field in tables.ordered_finite_fields:
        parents = tables.parent_fields[field]
        if parents:
            idx_tuple = tuple(out[p] for p in parents)
            pmf = tables.conditional_pmfs[field][idx_tuple]
        else:
            pmf = np.broadcast_to(
                tables.conditional_pmfs[field], (n, len(tables.categories[field]))
            )
        cum = np.cumsum(pmf, axis=1)
        cum[:, -1] = 1.0
        u = rng.random((n, 1))
        out[field] = np.argmax(u < cum, axis=1).astype(np.int32, copy=False)

    return out


def _lognormal_mu_sigma(mean: np.ndarray, std: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean_sq = mean**2
    var = std**2
    mu = np.log(mean_sq / np.sqrt(var + mean_sq))
    sigma = np.sqrt(np.log(1 + (std / mean) ** 2))
    return mu, sigma


def _init_distribution_arrays(
    dist: Distribution,
    n: int,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """Return mean, std, lower, upper, kind object array (kind: str or Distribution instance)."""
    mean = np.zeros(n, dtype=np.float64)
    std = np.zeros(n, dtype=np.float64)
    lower = np.full(n, -np.inf, dtype=np.float64)
    upper = np.full(n, np.inf, dtype=np.float64)
    kind = np.empty(n, dtype=object)

    if isinstance(dist, NormalDist):
        mean.fill(dist.mean)
        std.fill(dist.std)
        kind[:] = "normal"
    elif isinstance(dist, LogNormalDist):
        mean.fill(dist.mean)
        std.fill(dist.std)
        kind[:] = "lognormal"
    elif isinstance(dist, TruncatedNormalDist):
        mean.fill(dist.mean)
        std.fill(dist.std)
        lower.fill(dist.lower)
        upper.fill(dist.upper)
        kind[:] = "truncnorm"
    else:
        kind[:] = dist

    return mean, std, lower, upper, kind


def _apply_dist_to_mask(
    dist: Distribution,
    mask: np.ndarray,
    mean: np.ndarray,
    std: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    kind: np.ndarray,
) -> None:
    if not np.any(mask):
        return
    if isinstance(dist, NormalDist):
        mean[mask] = dist.mean
        std[mask] = dist.std
        kind[mask] = "normal"
    elif isinstance(dist, LogNormalDist):
        mean[mask] = dist.mean
        std[mask] = dist.std
        kind[mask] = "lognormal"
    elif isinstance(dist, TruncatedNormalDist):
        mean[mask] = dist.mean
        std[mask] = dist.std
        lower[mask] = dist.lower
        upper[mask] = dist.upper
        kind[mask] = "truncnorm"
    else:
        kind[mask] = dist


def sample_distribution_fields_batch(
    config: SamplingConfig,
    str_arrays: Dict[str, np.ndarray],
    n: int,
    rng: np.random.Generator,
) -> Dict[str, np.ndarray]:
    """
    Sample all distribution fields for n characters.

    str_arrays must contain numpy arrays (dtype=object) of shape (n,) with string
    category names for each finite field needed by overrides / transforms.
    """
    if n < 1:
        raise ValueError("n must be >= 1")

    cont: Dict[str, np.ndarray] = {}
    overrides: List = config.override_distributions or []

    for category, base_dist in config.base_probabilities_distributions.items():
        if not is_distribution(base_dist):
            raise TypeError(
                f"Expected Distribution for '{category}', got {type(base_dist)}"
            )

        mean, std, lower, upper, kind = _init_distribution_arrays(base_dist, n)
        matched = np.zeros(n, dtype=bool)

        for override in overrides:
            if override.field != category:
                continue
            m = np.ones(n, dtype=bool)
            for k, v in override.condition.items():
                m &= str_arrays[k] == v
            m &= ~matched
            if not np.any(m):
                continue
            if not is_distribution(override.distribution):
                raise TypeError(
                    f"Expected Distribution in override for '{category}', "
                    f"got {type(override.distribution)}"
                )
            _apply_dist_to_mask(
                override.distribution, m, mean, std, lower, upper, kind
            )
            matched |= m

        if category in config.transform_distributions:
            trait_map = config.transform_distributions[category]
            for trait_field, value_map in trait_map.items():
                trait_vals = str_arrays[trait_field]
                for trait_value, transform in value_map.items():
                    m = trait_vals == trait_value
                    if not np.any(m):
                        continue
                    ms = transform.mean_shift or 0.0
                    sm = transform.std_mult or 1.0
                    mean[m] += ms
                    std[m] *= sm

        out = np.empty(n, dtype=object)

        for label in ("normal", "lognormal", "truncnorm"):
            m = kind == label
            if not np.any(m):
                continue
            if label == "normal":
                out[m] = rng.normal(mean[m], std[m])
            elif label == "lognormal":
                mu, sigma = _lognormal_mu_sigma(mean[m], std[m])
                out[m] = rng.lognormal(mu, sigma)
            else:
                a = (lower[m] - mean[m]) / std[m]
                b = (upper[m] - mean[m]) / std[m]
                out[m] = truncnorm.rvs(
                    a,
                    b,
                    loc=mean[m],
                    scale=std[m],
                    random_state=rng,
                )

        slow_mask = np.ones(n, dtype=bool)
        for label in ("normal", "lognormal", "truncnorm"):
            slow_mask &= kind != label
        slow_idx = np.nonzero(slow_mask)[0]

        for i in slow_idx:
            dist_i = kind[i]
            if not is_distribution(dist_i):
                raise TypeError(
                    f"Expected Distribution for '{category}', got {type(dist_i)}"
                )
            field_value = 0.0
            if isinstance(dist_i, FunctionBasedDist):
                fn = dist_i.field_name
                if fn in cont:
                    field_value = float(cont[fn][i])
                elif fn in str_arrays:
                    raise TypeError(
                        f"FunctionBasedDist field {fn!r} refers to a categorical field; "
                        "expected a previously sampled numeric field."
                    )
            elif isinstance(dist_i, BernoulliBasedDist):
                fn = dist_i.field_name
                if fn in cont:
                    field_value = float(cont[fn][i])
            out[i] = _sample(dist_i, field_value)

        cont[category] = out

    return cont


def distribution_sample_to_python(value: object) -> Any:
    """Convert a numpy / scipy scalar from batch sampling to a plain Python value."""
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (np.floating, float)):
        return float(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    return value


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
    rng = np.random.default_rng()
    str_arrays = {
        k: np.asarray([sampled[k]], dtype=object)
        for k in config.base_probabilities_finite
        if k in sampled
    }
    cont = sample_distribution_fields_batch(config, str_arrays, 1, rng)
    for k, arr in cont.items():
        sampled[k] = distribution_sample_to_python(arr[0])
