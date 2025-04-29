"""
Holds the Pydantic BaseModels for various probaility distributions.
"""

from typing import List, Literal, Union

from pydantic import BaseModel


class NormalDist(BaseModel):
    type: Literal["normal"]
    mean: float
    std: float


Distribution = Union[NormalDist]
