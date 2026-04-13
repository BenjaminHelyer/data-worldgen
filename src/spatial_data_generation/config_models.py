from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field


class PlaneDomainConfig(BaseModel):
    type: Literal["plane"]
    metric: str
    bounds: Optional[list[list[float]]] = None


class SphereDomainConfig(BaseModel):
    type: Literal["sphere"]
    metric: str
    radius: float
    coordinate_system: Literal["lat_lon_degrees"]


class AbstractDomainConfig(BaseModel):
    type: Literal["abstract"]
    metric: str
    metadata: Optional[dict[str, Any]] = None


class PointGeometry(BaseModel):
    coordinates: list[float]


class PathGeometry(BaseModel):
    coordinates: list[list[float]]


class RegionGeometry(BaseModel):
    shell: list[list[float]]
    holes: Optional[list[list[list[float]]]] = None


class FeatureBase(BaseModel):
    id: str
    kind: str
    properties: Optional[dict[str, Any]] = None
    style: Optional[dict[str, Any]] = None


class PointFeatureConfig(FeatureBase):
    geometry_type: Literal["point"]
    geometry: PointGeometry


class PathFeatureConfig(FeatureBase):
    geometry_type: Literal["path"]
    geometry: PathGeometry


class RegionFeatureConfig(FeatureBase):
    geometry_type: Literal["region"]
    geometry: RegionGeometry


class NetworkNodeConfig(BaseModel):
    id: str
    feature_id: Optional[str] = None
    properties: Optional[dict[str, Any]] = None
    style: Optional[dict[str, Any]] = None


class NetworkEdgeConfig(BaseModel):
    id: str
    source: str
    target: str
    directed: bool = False
    weights: Optional[dict[str, float]] = None
    properties: Optional[dict[str, Any]] = None
    style: Optional[dict[str, Any]] = None


class NetworkConfig(BaseModel):
    nodes: list[NetworkNodeConfig]
    edges: list[NetworkEdgeConfig]
    metadata: Optional[dict[str, Any]] = None


class PortalConfig(BaseModel):
    id: str
    source_layer_id: str
    target_layer_id: str
    source_selector: dict[str, Any]
    target_selector: dict[str, Any]
    mapping: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None


class LayerConfig(BaseModel):
    id: str
    domain: Annotated[
        Union[PlaneDomainConfig, SphereDomainConfig, AbstractDomainConfig],
        Field(discriminator="type"),
    ]
    features: list[
        Annotated[
            Union[PointFeatureConfig, PathFeatureConfig, RegionFeatureConfig],
            Field(discriminator="geometry_type"),
        ]
    ]
    network: Optional[NetworkConfig] = None
    metadata: Optional[dict[str, Any]] = None


class WorldConfig(BaseModel):
    layers: list[LayerConfig]
    portals: list[PortalConfig]
    metadata: Optional[dict[str, Any]] = None

