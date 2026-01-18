"""
Core generic sampling and configuration abstractions.

This module provides domain-agnostic functionality for probabilistic sampling
that can be reused across different domains (population, ecosystem, etc.).
"""

from .config_protocol import SamplingConfig
from .sampling import (
    apply_factor_multipliers,
    sample_finite_fields,
    sample_distribution_fields_with_overrides,
)

__all__ = [
    "SamplingConfig",
    "apply_factor_multipliers",
    "sample_finite_fields",
    "sample_distribution_fields_with_overrides",
]
