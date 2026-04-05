"""
Core generic sampling and configuration abstractions.

This module provides domain-agnostic functionality for probabilistic sampling
that can be reused across different domains (population, ecosystem, etc.).
"""

from .config_protocol import SamplingConfig
from .finite_pmf import FiniteSamplingTables, build_finite_sampling_tables
from .sampling import (
    apply_factor_multipliers,
    get_finite_sampling_tables,
    sample_distribution_fields_batch,
    sample_distribution_fields_with_overrides,
    sample_finite_fields,
    sample_finite_fields_batch,
)

__all__ = [
    "SamplingConfig",
    "FiniteSamplingTables",
    "apply_factor_multipliers",
    "build_finite_sampling_tables",
    "get_finite_sampling_tables",
    "sample_distribution_fields_batch",
    "sample_distribution_fields_with_overrides",
    "sample_finite_fields",
    "sample_finite_fields_batch",
]
