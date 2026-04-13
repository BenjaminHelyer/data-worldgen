from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Optional

from spatial_data_generation.config_models import (
    AbstractDomainConfig,
    LayerConfig,
    PlaneDomainConfig,
    PortalConfig,
    SphereDomainConfig,
    WorldConfig,
)


class SpatialConfigError(ValueError):
    pass


def _ensure_unique(ids: Iterable[str], *, what: str) -> None:
    seen: set[str] = set()
    dups: set[str] = set()
    for x in ids:
        if x in seen:
            dups.add(x)
        seen.add(x)
    if dups:
        raise SpatialConfigError(f"Duplicate {what}: {sorted(dups)}")


def _domain_dimension(domain: object) -> Optional[int]:
    if isinstance(domain, PlaneDomainConfig):
        return 2
    if isinstance(domain, SphereDomainConfig):
        return 2
    if isinstance(domain, AbstractDomainConfig):
        return None
    return None


def _validate_feature_geometry_dims(layer: LayerConfig) -> None:
    expected_dim = _domain_dimension(layer.domain)
    if expected_dim is None:
        return

    def validate_point(coords: list[float], *, feature_id: str) -> None:
        if len(coords) != expected_dim:
            raise SpatialConfigError(
                f"Feature '{feature_id}' has coordinates dim {len(coords)} "
                f"but domain '{layer.domain.type}' expects {expected_dim}"
            )

    for feature in layer.features:
        if feature.geometry_type == "point":
            validate_point(feature.geometry.coordinates, feature_id=feature.id)
        elif feature.geometry_type == "path":
            for coords in feature.geometry.coordinates:
                validate_point(coords, feature_id=feature.id)
        elif feature.geometry_type == "region":
            if len(feature.geometry.shell) < 4:
                raise SpatialConfigError(
                    f"Feature '{feature.id}' region shell must have at least 4 points (including closure)"
                )
            if feature.geometry.shell[0] != feature.geometry.shell[-1]:
                raise SpatialConfigError(f"Feature '{feature.id}' region shell must be closed (first == last)")
            for coords in feature.geometry.shell:
                validate_point(coords, feature_id=feature.id)
            for hole in feature.geometry.holes or []:
                if len(hole) < 4:
                    raise SpatialConfigError(
                        f"Feature '{feature.id}' region hole must have at least 4 points (including closure)"
                    )
                if hole[0] != hole[-1]:
                    raise SpatialConfigError(
                        f"Feature '{feature.id}' region hole must be closed (first == last)"
                    )
                for coords in hole:
                    validate_point(coords, feature_id=feature.id)


def _validate_sphere_coordinate_convention(layer: LayerConfig) -> None:
    if not isinstance(layer.domain, SphereDomainConfig):
        return
    if layer.domain.coordinate_system != "lat_lon_degrees":
        raise SpatialConfigError(f"Unsupported sphere coordinate_system: {layer.domain.coordinate_system}")

    def validate_lat_lon(coords: list[float], *, feature_id: str) -> None:
        lat, lon = coords
        if not (-90.0 <= lat <= 90.0):
            raise SpatialConfigError(f"Feature '{feature_id}' has invalid latitude: {lat}")
        if not (-180.0 <= lon <= 180.0):
            raise SpatialConfigError(f"Feature '{feature_id}' has invalid longitude: {lon}")

    for feature in layer.features:
        if feature.geometry_type == "point":
            validate_lat_lon(feature.geometry.coordinates, feature_id=feature.id)
        elif feature.geometry_type == "path":
            for coords in feature.geometry.coordinates:
                validate_lat_lon(coords, feature_id=feature.id)
        elif feature.geometry_type == "region":
            for coords in feature.geometry.shell:
                validate_lat_lon(coords, feature_id=feature.id)
            for hole in feature.geometry.holes or []:
                for coords in hole:
                    validate_lat_lon(coords, feature_id=feature.id)


def _validate_plane_bounds(layer: LayerConfig) -> None:
    if not isinstance(layer.domain, PlaneDomainConfig):
        return
    if layer.domain.bounds is None:
        return
    b = layer.domain.bounds
    if len(b) != 2 or any(len(p) != 2 for p in b):
        raise SpatialConfigError(
            f"Layer '{layer.id}' plane bounds must be [[xmin,ymin],[xmax,ymax]]"
        )
    (xmin, ymin), (xmax, ymax) = b
    if not (xmin < xmax and ymin < ymax):
        raise SpatialConfigError(
            f"Layer '{layer.id}' plane bounds must satisfy xmin<xmax and ymin<ymax"
        )


def _validate_network(layer: LayerConfig) -> None:
    if layer.network is None:
        return
    _ensure_unique((n.id for n in layer.network.nodes), what=f"network node ids in layer '{layer.id}'")
    _ensure_unique((e.id for e in layer.network.edges), what=f"network edge ids in layer '{layer.id}'")

    node_ids = {n.id for n in layer.network.nodes}
    feature_ids = {f.id for f in layer.features}

    for node in layer.network.nodes:
        if node.feature_id is not None and node.feature_id not in feature_ids:
            raise SpatialConfigError(
                f"Network node '{node.id}' in layer '{layer.id}' references unknown feature_id '{node.feature_id}'"
            )

    for edge in layer.network.edges:
        if edge.source not in node_ids:
            raise SpatialConfigError(
                f"Network edge '{edge.id}' in layer '{layer.id}' has unknown source node '{edge.source}'"
            )
        if edge.target not in node_ids:
            raise SpatialConfigError(
                f"Network edge '{edge.id}' in layer '{layer.id}' has unknown target node '{edge.target}'"
            )


def _resolve_portal_source_feature(portal: PortalConfig, *, source_layer: LayerConfig) -> str:
    feature_id = portal.source_selector.get("feature_id")
    if not feature_id or not isinstance(feature_id, str):
        raise SpatialConfigError(f"Portal '{portal.id}' missing/invalid source_selector.feature_id")
    source_feature_ids = {f.id for f in source_layer.features}
    if feature_id not in source_feature_ids:
        raise SpatialConfigError(
            f"Portal '{portal.id}' source_selector.feature_id '{feature_id}' not found in layer '{source_layer.id}'"
        )
    return feature_id


def _validate_portal_target_selector(portal: PortalConfig, *, target_layer: LayerConfig) -> None:
    if portal.target_selector.get("layer_entry") is True:
        return
    feature_id = portal.target_selector.get("feature_id")
    if feature_id is None:
        raise SpatialConfigError(
            f"Portal '{portal.id}' target_selector must include 'layer_entry: true' or 'feature_id'"
        )
    if not isinstance(feature_id, str):
        raise SpatialConfigError(f"Portal '{portal.id}' has invalid target_selector.feature_id")
    target_feature_ids = {f.id for f in target_layer.features}
    if feature_id not in target_feature_ids:
        raise SpatialConfigError(
            f"Portal '{portal.id}' target_selector.feature_id '{feature_id}' not found in layer '{target_layer.id}'"
        )


@dataclass(frozen=True)
class _Graph:
    edges: dict[str, set[str]]


def _build_layer_graph(world: WorldConfig) -> _Graph:
    edges: dict[str, set[str]] = defaultdict(set)
    for portal in world.portals:
        edges[portal.source_layer_id].add(portal.target_layer_id)
    return _Graph(edges=dict(edges))


def _assert_acyclic(graph: _Graph) -> None:
    visited: set[str] = set()
    in_stack: set[str] = set()

    def dfs(node: str) -> None:
        if node in in_stack:
            raise SpatialConfigError("Portal-induced layer graph has a cycle")
        if node in visited:
            return
        visited.add(node)
        in_stack.add(node)
        for nxt in graph.edges.get(node, set()):
            dfs(nxt)
        in_stack.remove(node)

    for node in list(graph.edges.keys()):
        dfs(node)


def validate_world(world: WorldConfig) -> None:
    _ensure_unique((layer.id for layer in world.layers), what="layer ids")
    _ensure_unique((portal.id for portal in world.portals), what="portal ids")

    layers_by_id = {layer.id: layer for layer in world.layers}

    for layer in world.layers:
        _ensure_unique((f.id for f in layer.features), what=f"feature ids in layer '{layer.id}'")
        _validate_plane_bounds(layer)
        _validate_feature_geometry_dims(layer)
        _validate_sphere_coordinate_convention(layer)
        _validate_network(layer)

    for portal in world.portals:
        if portal.source_layer_id not in layers_by_id:
            raise SpatialConfigError(
                f"Portal '{portal.id}' references unknown source_layer_id '{portal.source_layer_id}'"
            )
        if portal.target_layer_id not in layers_by_id:
            raise SpatialConfigError(
                f"Portal '{portal.id}' references unknown target_layer_id '{portal.target_layer_id}'"
            )
        source_layer = layers_by_id[portal.source_layer_id]
        target_layer = layers_by_id[portal.target_layer_id]
        _resolve_portal_source_feature(portal, source_layer=source_layer)
        _validate_portal_target_selector(portal, target_layer=target_layer)

    _assert_acyclic(_build_layer_graph(world))

