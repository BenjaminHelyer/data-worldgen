"""
Precomputed conditional PMF tables for finite (categorical) fields.

Built once per SamplingConfig instance (cached via weak references in sampling.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np

from .config_protocol import SamplingConfig


@dataclass(frozen=True)
class FiniteSamplingTables:
    """Vectorized lookup tables for categorical sampling."""

    ordered_finite_fields: Tuple[str, ...]
    categories: Dict[str, Tuple[str, ...]]
    category_to_index: Dict[str, Dict[str, int]]
    parent_fields: Dict[str, Tuple[str, ...]]
    conditional_pmfs: Dict[str, np.ndarray]


def finite_field_sampling_order(config: SamplingConfig) -> Tuple[str, ...]:
    """Match sample_finite_fields ordering: factor keys first, then remaining finite fields."""
    finite_fields = list(config.base_probabilities_finite.keys())
    ordered = [field for field in config.factors if field in finite_fields]
    ordered += [field for field in finite_fields if field not in ordered]
    return tuple(ordered)


def parents_for_field(config: SamplingConfig, target_field: str) -> Tuple[str, ...]:
    """Source fields that influence target_field (insertion order of factors keys)."""
    factors = config.factors
    return tuple(src for src in factors if target_field in factors[src])


def parent_value_domain(
    config: SamplingConfig, parent_field: str, target_field: str
) -> Tuple[str, ...]:
    """
    Ordered category labels for a parent when indexing conditional PMFs.

    Uses base_probabilities_finite when present; otherwise keys from the factor
    map for this parent-target edge (same values apply_factor_multipliers can see).
    """
    if parent_field in config.base_probabilities_finite:
        return tuple(config.base_probabilities_finite[parent_field].keys())
    sub = config.factors[parent_field][target_field]
    return tuple(sub.keys())


def build_finite_sampling_tables(config: SamplingConfig) -> FiniteSamplingTables:
    """
    Precompute normalized conditional PMF tensors for every finite field.

    For target T with parents S1..Sm (in factors dict order), the table has shape
    (|S1|, ..., |Sm|, |T|); each last-axis slice sums to 1 (when the unnormed mass is positive).
    """
    ordered = finite_field_sampling_order(config)
    categories: Dict[str, Tuple[str, ...]] = {}
    category_to_index: Dict[str, Dict[str, int]] = {}

    for field in ordered:
        base = config.base_probabilities_finite[field]
        cats = tuple(base.keys())
        categories[field] = cats
        category_to_index[field] = {c: i for i, c in enumerate(cats)}

    for field in ordered:
        for p in parents_for_field(config, field):
            if p not in category_to_index:
                dom = parent_value_domain(config, p, field)
                categories[p] = dom
                category_to_index[p] = {c: i for i, c in enumerate(dom)}

    parent_fields: Dict[str, Tuple[str, ...]] = {}
    conditional_pmfs: Dict[str, np.ndarray] = {}

    for field in ordered:
        base_probs = config.base_probabilities_finite[field]
        target_cats = categories[field]
        k = len(target_cats)
        base_vec = np.array([base_probs[c] for c in target_cats], dtype=np.float64)
        parents = parents_for_field(config, field)
        parent_fields[field] = parents

        if not parents:
            total = float(base_vec.sum())
            if total > 0:
                conditional_pmfs[field] = base_vec / total
            else:
                conditional_pmfs[field] = np.full(k, 1.0 / k, dtype=np.float64)
            continue

        m = len(parents)
        parent_sizes = tuple(len(categories[p]) for p in parents)
        table = np.broadcast_to(
            base_vec.reshape((1,) * m + (k,)), parent_sizes + (k,)
        ).copy()

        for dim, src in enumerate(parents):
            src_cats = categories[src]
            n_src = len(src_cats)
            fac = np.ones((n_src, k), dtype=np.float64)
            sub = config.factors[src][field]
            for i, sv in enumerate(src_cats):
                row = sub.get(sv, {})
                for j, tv in enumerate(target_cats):
                    if tv in row:
                        fac[i, j] = row[tv]
            exp = [1] * m
            exp[dim] = n_src
            fac_b = fac.reshape(tuple(exp) + (k,))
            table *= fac_b

        sums = table.sum(axis=-1, keepdims=True)
        sums = np.where(sums > 0, sums, 1.0)
        conditional_pmfs[field] = table / sums

    return FiniteSamplingTables(
        ordered_finite_fields=ordered,
        categories=categories,
        category_to_index=category_to_index,
        parent_fields=parent_fields,
        conditional_pmfs=conditional_pmfs,
    )
