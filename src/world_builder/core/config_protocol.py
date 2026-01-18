"""
Protocol defining the interface for sampling configurations.

Any config class that implements this protocol can be used with the generic
sampling functions in core.sampling.
"""

from typing import Protocol, Dict, List, Optional

from world_builder.distributions_config import (
    Distribution,
    DistributionOverride,
    DistributionTransformMap,
)


class SamplingConfig(Protocol):
    """
    Protocol that any sampling configuration must implement.

    This allows the generic sampling functions to work with any config type
    that has the required attributes, enabling code reuse across domains.

    Example implementation for an ecosystem model:

    Attributes:
        base_probabilities_finite: Required mapping of field names to probability
            distributions. Each inner dict maps possible values to their probabilities,
            which must sum to 1.0.

            Example: ``{"species": {"rabbit": 0.5, "fox": 0.3, "hawk": 0.2}}``
            defines three species with their base probabilities.

        base_probabilities_distributions: Required mapping of field names to continuous
            distribution objects.

            Example:
                ``{"population_size": NormalDist(type="normal", mean=100, std=20)}``
            defines a population size field drawn from a normal distribution.

        factors: Optional nested dictionary defining conditional probability multipliers.
            Structure:
                ``factor_field -> target_field -> factor_value -> {target_value: multiplier}``.

            Example:
                ``{"habitat": {"species": {"forest": {"fox": 2.0}}}}`` means
            "if habitat is forest, multiply the probability of species being fox by 2.0".
            Can be empty dict if no factors are needed.

        override_distributions: Optional list of distribution overrides that replace
            base distributions when specific conditions are met.
            Can be None if no overrides are needed.

            Example: Override population_size distribution for hawks to have a different mean.

        transform_distributions: Optional mapping for applying transformations to
            distributions based on trait values.
            Structure:
                ``distribution_field -> trait_field -> trait_value -> transform``.
            Example:
                ``{"population_size": {"habitat": {"wetland":
                DistributionTransformOperation(mean_shift=-30.0)}}}``
            shifts the mean of population_size by -30 when habitat is wetland.
            Can be empty dict if no transformations are needed.

        metadata: Optional dictionary of constant string key-value pairs that are
            copied directly to sampled entities.
            Example: ``{"ecosystem_name": "Northwood Reserve"}``.
            Can be empty dict if no metadata is needed.
    """

    # finite categorical fields with probabilities that sum to 1.0
    base_probabilities_finite: Dict[str, Dict[str, float]]

    # continuous fields defined by distributions
    base_probabilities_distributions: Dict[str, Distribution]

    # (optional) factor graph multipliers for conditional probabilities
    factors: Dict[str, Dict[str, Dict[str, Dict[str, float]]]]

    # (optional) conditional distribution overrides
    override_distributions: Optional[List[DistributionOverride]]

    # (optional) distribution transformations based on trait values
    transform_distributions: DistributionTransformMap

    # (optional) constant metadata fields
    metadata: Dict[str, str]
