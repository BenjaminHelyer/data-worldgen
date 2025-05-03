"""
Holds the Pydantic BaseModels and distribution objects for various probaility distributions.
"""

import random

from typing import Literal, Union, Dict, Any

from pydantic import BaseModel, Field


class NormalDist(BaseModel):
    type: Literal["normal"]
    mean: float
    std: float


class LogNormalDist(BaseModel):
    type: Literal["lognormal"]
    mean: float
    std: float


Distribution = Union[NormalDist, LogNormalDist]

DISTRIBUTION_REGISTRY: Dict[str, BaseModel] = {
    "normal": NormalDist,
    "lognormal": LogNormalDist,  # NEW
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
    """
    if isinstance(dist, NormalDist):
        return random.gauss(dist.mean, dist.std)
    elif isinstance(dist, LogNormalDist):
        return random.lognormvariate(dist.mean, dist.std)  # NEW
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
