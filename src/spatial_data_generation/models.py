"""Core abstractions for multiscale spatial data generation.

The schema follows the design in ``SPATIAL_DATA_OVERVIEW.md``:

- Layer = (Domain, Features, Network)
- World = (Layers, Portals)

Geometry, topology, and hierarchy are modeled independently and composed at the
layer/world level.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class DomainKind(str, Enum):
    """Kinds of spatial domains (underlying spaces)."""

    PLANE = "plane"
    SPHERE = "sphere"
    GRAPH = "graph"


class GeometryType(str, Enum):
    """Embedded geometry types for features."""

    POINT = "point"
    PATH = "path"
    REGION = "region"


class Domain(BaseModel):
    """Metric space domain for a layer."""

    kind: DomainKind
    metric: str
    dimension: int = Field(ge=1)
    bounds: dict[str, list[float]] | None = None
    atlas: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_domain(self) -> "Domain":
        if self.kind == DomainKind.PLANE:
            if self.dimension != 2:
                raise ValueError("plane domains must have dimension=2")
            if self.bounds is not None:
                mins = self.bounds.get("min")
                maxs = self.bounds.get("max")
                if mins is None or maxs is None:
                    raise ValueError("plane bounds must include min/max vectors")
                if len(mins) != self.dimension or len(maxs) != self.dimension:
                    raise ValueError("plane bounds must match domain dimension")
                if any(lo >= hi for lo, hi in zip(mins, maxs, strict=True)):
                    raise ValueError("each min bound must be < max bound")

        if self.kind == DomainKind.SPHERE:
            if self.dimension != 2:
                raise ValueError("sphere domains must have dimension=2 (lat/lon)")
            if self.metric.lower() not in {"geodesic", "haversine", "great_circle"}:
                raise ValueError("sphere domains require a geodesic metric")

        if self.kind == DomainKind.GRAPH and self.bounds is not None:
            raise ValueError("graph domains should not define coordinate bounds")

        return self


class Geometry(BaseModel):
    """Geometry embedded in a domain."""

    type: GeometryType
    coordinates: list[list[float]]

    @field_validator("coordinates")
    @classmethod
    def non_empty_coordinates(cls, value: list[list[float]]) -> list[list[float]]:
        if not value:
            raise ValueError("coordinates cannot be empty")
        return value


class Feature(BaseModel):
    """Semantic object embedded in a domain."""

    id: str
    kind: str
    geometry: Geometry
    properties: dict[str, Any] = Field(default_factory=dict)
    style: dict[str, Any] = Field(default_factory=dict)


class NetworkNode(BaseModel):
    """Node in a traversal network."""

    id: str
    position: list[float] | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class NetworkEdge(BaseModel):
    """Edge in a traversal network."""

    source: str
    target: str
    cost: float = Field(default=1.0, gt=0)
    properties: dict[str, Any] = Field(default_factory=dict)


class Network(BaseModel):
    """Topology over a layer domain/features."""

    nodes: list[NetworkNode] = Field(default_factory=list)
    edges: list[NetworkEdge] = Field(default_factory=list)
    directed: bool = True

    @model_validator(mode="after")
    def validate_endpoints(self) -> "Network":
        node_ids = {node.id for node in self.nodes}
        for edge in self.edges:
            if edge.source not in node_ids or edge.target not in node_ids:
                raise ValueError(
                    f"edge ({edge.source} -> {edge.target}) references unknown node"
                )
        return self


class Layer(BaseModel):
    """Layer = (Domain, Features, Network)."""

    id: str
    domain: Domain
    features: list[Feature] = Field(default_factory=list)
    network: Network | None = None

    @model_validator(mode="after")
    def validate_embeddings(self) -> "Layer":
        mins = maxs = None
        if self.domain.bounds is not None:
            mins = self.domain.bounds.get("min")
            maxs = self.domain.bounds.get("max")

        for feature in self.features:
            coords = feature.geometry.coordinates

            if feature.geometry.type == GeometryType.POINT and len(coords) != 1:
                raise ValueError(f"feature {feature.id}: point geometries must have 1 coordinate")
            if feature.geometry.type == GeometryType.PATH and len(coords) < 2:
                raise ValueError(f"feature {feature.id}: path geometries must have >=2 coordinates")
            if feature.geometry.type == GeometryType.REGION and len(coords) < 3:
                raise ValueError(f"feature {feature.id}: region geometries must have >=3 coordinates")

            for point in coords:
                if len(point) != self.domain.dimension:
                    raise ValueError(
                        f"feature {feature.id}: coordinate dimension {len(point)} != domain "
                        f"dimension {self.domain.dimension}"
                    )
                if self.domain.kind == DomainKind.SPHERE:
                    lat, lon = point
                    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                        raise ValueError(
                            f"feature {feature.id}: sphere coords must be [lat, lon]"
                        )
                if mins is not None and maxs is not None:
                    for val, lo, hi in zip(point, mins, maxs, strict=True):
                        if not (lo <= val <= hi):
                            raise ValueError(
                                f"feature {feature.id}: coordinate {point} outside bounds"
                            )

        if self.network is not None:
            for node in self.network.nodes:
                if node.position is None:
                    continue
                if len(node.position) != self.domain.dimension:
                    raise ValueError(
                        f"node {node.id}: position dimension {len(node.position)} != "
                        f"domain dimension {self.domain.dimension}"
                    )

        return self


class Portal(BaseModel):
    """Local mapping between subsets of two layers."""

    id: str
    source_layer_id: str
    target_layer_id: str
    source_feature_id: str | None = None
    target_feature_id: str | None = None
    mapping_kind: str = "local_map"
    properties: dict[str, Any] = Field(default_factory=dict)


class World(BaseModel):
    """World = (Layers, Portals) with portal hierarchy as DAG."""

    layers: list[Layer]
    portals: list[Portal] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_world(self) -> "World":
        layer_by_id = {layer.id: layer for layer in self.layers}
        edges: dict[str, set[str]] = {layer.id: set() for layer in self.layers}

        for portal in self.portals:
            if portal.source_layer_id not in layer_by_id:
                raise ValueError(f"unknown source layer: {portal.source_layer_id}")
            if portal.target_layer_id not in layer_by_id:
                raise ValueError(f"unknown target layer: {portal.target_layer_id}")
            edges[portal.source_layer_id].add(portal.target_layer_id)

            if portal.source_feature_id is not None:
                source_ids = {f.id for f in layer_by_id[portal.source_layer_id].features}
                if portal.source_feature_id not in source_ids:
                    raise ValueError(
                        f"portal {portal.id} references unknown source feature "
                        f"{portal.source_feature_id}"
                    )

            if portal.target_feature_id is not None:
                target_ids = {f.id for f in layer_by_id[portal.target_layer_id].features}
                if portal.target_feature_id not in target_ids:
                    raise ValueError(
                        f"portal {portal.id} references unknown target feature "
                        f"{portal.target_feature_id}"
                    )

        visited: set[str] = set()
        stack: set[str] = set()

        def dfs(layer_id: str) -> bool:
            if layer_id in stack:
                return True
            if layer_id in visited:
                return False
            visited.add(layer_id)
            stack.add(layer_id)
            for nxt in edges[layer_id]:
                if dfs(nxt):
                    return True
            stack.remove(layer_id)
            return False

        for layer in self.layers:
            if dfs(layer.id):
                raise ValueError("portal hierarchy must be acyclic")

        return self
