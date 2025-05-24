"""
Holds the Pydantic BaseModels and distribution objects for various probaility distributions.
"""

from typing import Literal, Union, Dict, Any, Protocol, List
import random
import math

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


class MultiLinearParams(FunctionParams):
    """Parameters for multi-linear function: sum(coefficients[field] * field_value) + intercept."""

    fields: List[str] = Field(
        description="List of field names this function depends on"
    )
    coefficients: Dict[str, float] = Field(description="Coefficient for each field")
    intercept: float

    @model_validator(mode="after")
    def validate_coefficients(self) -> "MultiLinearParams":
        """Validate that coefficients match the fields."""
        if set(self.fields) != set(self.coefficients.keys()):
            raise ValueError("Fields and coefficients keys must match exactly")
        return self


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

    type: Literal["constant", "linear", "exponential", "quadratic", "multi_linear"]
    params: Union[
        ConstantParams,
        LinearParams,
        ExponentialParams,
        QuadraticParams,
        MultiLinearParams,
    ]

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
        if self.type == "multi_linear" and not isinstance(
            self.params, MultiLinearParams
        ):
            raise ValueError("Multi-linear function requires MultiLinearParams")
        return self

    def get_required_fields(self) -> List[str]:
        """Return the list of fields this function depends on."""
        if self.type == "multi_linear":
            return self.params.fields
        else:
            # Single-variable functions don't specify required fields here
            # They depend on the field_name in the distribution configuration
            return []


class NoiseFunctionConfig(BaseModel):
    """Configuration for the noise function."""

    model_config = ConfigDict(frozen=True)

    type: Literal["normal", "lognormal", "truncated_normal"]
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
        if self.type == "truncated_normal":
            if "lower" not in self.params or "upper" not in self.params:
                raise ValueError("truncated_normal requires lower and upper bounds")
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


class BernoulliBasedDist(BaseModel):
    """
    Configuration for a Bernoulli distribution where the probability parameter
    is determined by a function of some field value (e.g. age).

    This is a simplified distribution that only uses a mean_function
    to determine the probability parameter, which is then used as the
    parameter of a Bernoulli trial.

    Attributes:
        field_name: The character field to use as input (e.g. 'age')
        mean_function: Function that determines the probability parameter
    """

    model_config = ConfigDict(frozen=True)

    field_name: str
    mean_function: FunctionConfig


Distribution = Union[
    NormalDist,
    LogNormalDist,
    TruncatedNormalDist,
    FunctionBasedDist,
    BernoulliBasedDist,
]

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

    dist_type = config.get("type")
    if dist_type is None:
        raise ValueError("Config must specify a 'type' field")

    if dist_type == "function_based":
        return FunctionBasedDist(**config)
    elif dist_type not in DISTRIBUTION_REGISTRY:
        raise ValueError(f"Unsupported distribution type: {dist_type}")

    model_cls = DISTRIBUTION_REGISTRY[dist_type]
    return model_cls(**config)


def _evaluate_function(
    func: FunctionConfig, field_values: Union[float, Dict[str, float]]
) -> float:
    """
    Helper function to evaluate a function configuration.

    Args:
        func: The function configuration to evaluate
        field_values: Either a single float for single-variable functions,
                     or a dictionary of field_name -> value for multi-variable functions

    Returns:
        The evaluated function value
    """
    if func.type == "constant":
        return func.params.value
    elif func.type == "linear":
        if not isinstance(field_values, (int, float)):
            raise ValueError("Linear function requires a single numeric input")
        return func.params.slope * field_values + func.params.intercept
    elif func.type == "exponential":
        if not isinstance(field_values, (int, float)):
            raise ValueError("Exponential function requires a single numeric input")
        return func.params.base * math.exp(func.params.rate * field_values)
    elif func.type == "quadratic":
        if not isinstance(field_values, (int, float)):
            raise ValueError("Quadratic function requires a single numeric input")
        return (
            func.params.a * (field_values**2)
            + func.params.b * field_values
            + func.params.c
        )
    elif func.type == "multi_linear":
        if not isinstance(field_values, dict):
            raise ValueError(
                "Multi-linear function requires a dictionary of field values"
            )
        result = func.params.intercept
        for field in func.params.fields:
            if field not in field_values:
                raise ValueError(
                    f"Missing required field '{field}' for multi-linear function"
                )
            result += func.params.coefficients[field] * field_values[field]
        return result
    else:
        raise ValueError(f"Unsupported function type: {func.type}")


def _sample(dist: Distribution, field_value: float = 0) -> float:
    """
    Draw a random sample from a distribution model instance.
    Uses Python's random module for consistency across all distributions.
    """
    if isinstance(dist, NormalDist):
        return random.gauss(dist.mean, dist.std)
    elif isinstance(dist, LogNormalDist):
        # For lognormal, we need to adjust the parameters to prevent overflow
        # Using the relationship between normal and lognormal parameters
        mu = math.log(dist.mean**2 / math.sqrt(dist.std**2 + dist.mean**2))
        sigma = math.sqrt(math.log(1 + (dist.std / dist.mean) ** 2))
        return random.lognormvariate(mu, sigma)
    elif isinstance(dist, TruncatedNormalDist):
        a = (dist.lower - dist.mean) / dist.std
        b = (dist.upper - dist.mean) / dist.std
        # Use Python's random module to generate uniform random numbers for scipy
        rng = np.random.RandomState(random.randint(0, 2**32 - 1))
        return float(
            truncnorm.rvs(a, b, loc=dist.mean, scale=dist.std, random_state=rng)
        )
    elif isinstance(dist, FunctionBasedDist):
        # First calculate the mean value
        mean_value = _evaluate_function(dist.mean_function, field_value)

        # Then add the noise
        if dist.noise_function.type == "normal":
            scale = dist.noise_function.params["scale_factor"]
            if isinstance(scale, FunctionConfig):
                scale_value = _evaluate_function(scale, field_value)
            else:
                scale_value = scale
            return mean_value + random.gauss(0, scale_value)
        elif dist.noise_function.type == "lognormal":
            scale = dist.noise_function.params["scale_factor"]
            if isinstance(scale, FunctionConfig):
                scale_value = _evaluate_function(scale, field_value)
            else:
                scale_value = scale

            # For lognormal noise, we use a different parameterization to handle large values
            # We want the noise to be multiplicative rather than additive for large values
            noise_factor = math.exp(
                random.gauss(0, math.log1p(scale_value / mean_value))
            )
            return mean_value * noise_factor
        elif dist.noise_function.type == "truncated_normal":
            scale = dist.noise_function.params["scale_factor"]
            if isinstance(scale, FunctionConfig):
                scale_value = _evaluate_function(scale, field_value)
            else:
                scale_value = scale
            lower = dist.noise_function.params["lower"]
            upper = dist.noise_function.params["upper"]
            # Generate noise between lower and upper bounds
            rng = np.random.RandomState(random.randint(0, 2**32 - 1))
            noise = float(
                truncnorm.rvs(
                    (lower - 0) / scale_value,  # a = (lower - loc) / scale
                    (upper - 0) / scale_value,  # b = (upper - loc) / scale
                    loc=0,  # center at 0
                    scale=scale_value,
                    random_state=rng,
                )
            )
            if noise < 0:
                raise ValueError(
                    f"Got negative noise value: {noise} for truncated normal with lower={lower}"
                )
            return mean_value + noise
        raise NotImplementedError(
            f"FunctionBasedDist sampling not implemented for noise type: {dist.noise_function.type}"
        )
    elif isinstance(dist, BernoulliBasedDist):
        # For Bernoulli distribution, we use the probability parameter from the mean_function
        probability = _evaluate_function(dist.mean_function, field_value)
        # Ensure probability is between 0 and 1
        probability = max(0.0, min(1.0, probability))
        return random.random() < probability
    raise ValueError(f"No sampler implemented for distribution type: {type(dist)}")


def sample_from_config(config: dict, field_value: float = 0) -> float:
    """
    Convenience method: parse config dict and draw a sample.
    """
    dist = _parse(config)
    return _sample(dist, field_value)


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
