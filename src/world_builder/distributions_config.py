"""
Holds the Pydantic BaseModels and distribution objects for various probaility distributions.
"""

from typing import Literal, Union, Dict, Any, Protocol
import random

import numpy as np
from pydantic import BaseModel, Field, ConfigDict, model_validator
from scipy.stats import truncnorm


class FunctionParams(BaseModel):
    """Base class for function parameters."""

    model_config = ConfigDict(frozen=True)


class ConstantParams(FunctionParams):
    """Parameters for constant function."""

    value: float


class LinearParams(FunctionParams):
    """Parameters for linear function."""

    slope: float
    intercept: float


class ExponentialParams(FunctionParams):
    """Parameters for exponential function."""

    base: float
    rate: float


class QuadraticParams(FunctionParams):
    """Parameters for quadratic function."""

    a: float
    b: float
    c: float


class FunctionConfig(BaseModel):
    """Configuration for a mathematical function."""

    model_config = ConfigDict(frozen=True)

    type: Literal["constant", "linear", "exponential", "quadratic"]
    params: Union[ConstantParams, LinearParams, ExponentialParams, QuadraticParams]

    @model_validator(mode="after")
    def validate_params(self) -> "FunctionConfig":
        """Validate that params match the function type."""
        if self.type == "constant" and not isinstance(self.params, ConstantParams):
            raise ValueError("Constant function requires ConstantParams")
        if self.type == "linear" and not isinstance(self.params, LinearParams):
            raise ValueError("Linear function requires LinearParams")
        if self.type == "exponential" and not isinstance(
            self.params, ExponentialParams
        ):
            raise ValueError("Exponential function requires ExponentialParams")
        if self.type == "quadratic" and not isinstance(self.params, QuadraticParams):
            raise ValueError("Quadratic function requires QuadraticParams")
        return self


class NoiseFunctionConfig(BaseModel):
    """Configuration for the noise function."""

    model_config = ConfigDict(frozen=True)

    type: Literal["normal"]
    params: Dict[str, Any] = Field(
        description="Parameters for the noise function, including field_name and scale_factor"
    )

    @model_validator(mode="after")
    def validate_params(self) -> "NoiseFunctionConfig":
        """Validate noise function parameters."""
        if "field_name" not in self.params:
            raise ValueError("Noise function must specify field_name")
        if "scale_factor" not in self.params:
            raise ValueError("Noise function must specify scale_factor")
        if not isinstance(self.params["scale_factor"], (dict, FunctionConfig)):
            raise ValueError("scale_factor must be a function configuration")
        if isinstance(self.params["scale_factor"], dict):
            self.params["scale_factor"] = FunctionConfig(**self.params["scale_factor"])
        return self


class FunctionBasedDist(BaseModel):
    """Configuration for a profession's net worth calculation."""

    model_config = ConfigDict(frozen=True)

    field_name: str
    mean_function: FunctionConfig
    noise_function: NoiseFunctionConfig


class DistributionTransformOperation(BaseModel):
    """
    Defines a transformation operation that can be applied to a distribution.

    Attributes:
        mean_shift: Optional amount to shift the mean by (additive)
        std_mult: Optional amount to multiply the standard deviation by
    """

    mean_shift: float | None = None
    std_mult: float | None = None


class TransformableDistribution(Protocol):
    """Protocol defining distributions that can be transformed."""

    def with_transform(
        self, transform: DistributionTransformOperation
    ) -> "TransformableDistribution":
        """
        Returns a new distribution with the transform applied.

        Args:
            transform: The transformation operation to apply

        Returns:
            A new distribution with the transformation applied
        """
        ...


class NormalDist(BaseModel):
    """
    Normal (Gaussian) distribution.

    Attributes:
        type: Literal "normal" to identify this distribution type
        mean: Mean (μ) of the distribution
        std: Standard deviation (σ) of the distribution
    """

    type: Literal["normal"]
    mean: float
    std: float

    def with_transform(self, transform: DistributionTransformOperation) -> "NormalDist":
        """
        Returns a new normal distribution with the transform applied.

        Args:
            transform: The transformation operation to apply

        Returns:
            A new NormalDist with shifted mean and/or scaled standard deviation
        """
        return self.model_copy(
            update={
                "mean": self.mean + (transform.mean_shift or 0.0),
                "std": self.std * (transform.std_mult or 1.0),
            }
        )


class LogNormalDist(BaseModel):
    """
    Log-normal distribution.

    Attributes:
        type: Literal "lognormal" to identify this distribution type
        mean: Mean (μ) of the underlying normal distribution
        std: Standard deviation (σ) of the underlying normal distribution
    """

    type: Literal["lognormal"]
    mean: float
    std: float

    def with_transform(
        self, transform: DistributionTransformOperation
    ) -> "LogNormalDist":
        """
        Returns a new log-normal distribution with the transform applied.

        Args:
            transform: The transformation operation to apply

        Returns:
            A new LogNormalDist with shifted mean and/or scaled standard deviation
        """
        return self.model_copy(
            update={
                "mean": self.mean + (transform.mean_shift or 0.0),
                "std": self.std * (transform.std_mult or 1.0),
            }
        )


class TruncatedNormalDist(BaseModel):
    """
    Truncated normal distribution - a normal distribution bounded by lower and upper limits.

    Attributes:
        type: Literal "truncated_normal" to identify this distribution type
        mean: Mean (μ) of the underlying normal distribution
        std: Standard deviation (σ) of the underlying normal distribution
        lower: Lower bound (inclusive) for truncation
        upper: Upper bound (inclusive) for truncation, defaults to positive infinity
    """

    type: Literal["truncated_normal"]
    mean: float
    std: float
    lower: float = Field(description="Lower bound (inclusive)")
    upper: float = Field(float("inf"), description="Upper bound (inclusive)")

    def with_transform(
        self, transform: DistributionTransformOperation
    ) -> "TruncatedNormalDist":
        """
        Returns a new truncated normal distribution with the transform applied.

        Args:
            transform: The transformation operation to apply

        Returns:
            A new TruncatedNormalDist with shifted mean and/or scaled standard deviation
        """
        return self.model_copy(
            update={
                "mean": self.mean + (transform.mean_shift or 0.0),
                "std": self.std * (transform.std_mult or 1.0),
            }
        )


# Maps values like "Mos Eisley" or "Wookiee" to transforms
DistributionTransformCondition = Dict[str, DistributionTransformOperation]

# Maps fields like "city", "species" to their value->transform mappings
DistributionTransformField = Dict[str, DistributionTransformCondition]

# Maps target distribution fields like "age" to the field-based conditions
DistributionTransformMap = Dict[str, DistributionTransformField]


Distribution = Union[NormalDist, LogNormalDist, TruncatedNormalDist, FunctionBasedDist]

DISTRIBUTION_REGISTRY: Dict[str, BaseModel] = {
    "normal": NormalDist,
    "lognormal": LogNormalDist,
    "truncated_normal": TruncatedNormalDist,
}


def _parse(config: Any) -> Distribution:
    """
    Parse a config dict or BaseModel into the appropriate distribution model.
    Raises ValidationError if config is invalid or type is unsupported.
    """
    if isinstance(config, BaseModel):
        return config

    if not isinstance(config, dict):
        raise TypeError(f"Config must be a dict or BaseModel, got {type(config)}")

    dist_type = (
        config.type
    )  # note that the key in config of 'type' is a distribution type, e.g., 'normal' or 'binomial', not a Python language type
    if dist_type not in DISTRIBUTION_REGISTRY:
        raise ValueError(f"Unsupported distribution type: {dist_type}")

    model_cls = DISTRIBUTION_REGISTRY[dist_type]
    return model_cls(**config)


def _sample(dist: Distribution) -> float:
    """
    Draw a random sample from a distribution model instance.
    Uses Python's random module for consistency across all distributions.
    """
    if isinstance(dist, NormalDist):
        return random.gauss(dist.mean, dist.std)
    elif isinstance(dist, LogNormalDist):
        return random.lognormvariate(dist.mean, dist.std)
    elif isinstance(dist, TruncatedNormalDist):
        a = (dist.lower - dist.mean) / dist.std
        b = (dist.upper - dist.mean) / dist.std
        # Use Python's random module to generate uniform random numbers for scipy
        rng = np.random.RandomState(random.randint(0, 2**32 - 1))
        return float(
            truncnorm.rvs(a, b, loc=dist.mean, scale=dist.std, random_state=rng)
        )
    elif isinstance(dist, FunctionBasedDist):
        raise NotImplementedError("FunctionBasedDist sampling not implemented yet")
    raise ValueError(f"No sampler implemented for distribution type: {dist.type}")


def sample_from_config(config: dict) -> float:
    """
    Convenience method: parse config dict and draw a sample.
    """
    dist = _parse(config)
    return _sample(dist)


class DistributionOverride(BaseModel):
    """
    Represents a conditional override of a base distribution.

    For example, we might draw 'age' from a different distribution if 'profession' is 'soldier'.
    """

    condition: Dict[str, str] = Field(
        description="Condition dict, e.g., {'profession': 'soldier'}."
    )
    field: str = Field(
        description="Field in base_probabilities_distributions to override, e.g., 'age'."
    )
    distribution: Distribution = Field(
        description="Replacement distribution when condition is matched."
    )
