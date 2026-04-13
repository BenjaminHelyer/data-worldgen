from __future__ import annotations

from typing import Iterable, Optional

from matplotlib.figure import Figure

from spatial_data_generation.config_models import (
    AbstractDomainConfig,
    LayerConfig,
    PlaneDomainConfig,
    SphereDomainConfig,
    WorldConfig,
)


def _plane_xy(coords: list[float]) -> tuple[float, float]:
    return float(coords[0]), float(coords[1])


def _sphere_xy_lat_lon(coords: list[float]) -> tuple[float, float]:
    lat, lon = float(coords[0]), float(coords[1])
    return lon, lat


def _iter_feature_points(layer: LayerConfig) -> Iterable[tuple[str, tuple[float, float]]]:
    if isinstance(layer.domain, SphereDomainConfig):
        to_xy = _sphere_xy_lat_lon
    else:
        to_xy = _plane_xy

    for f in layer.features:
        if f.geometry_type == "point":
            yield f.id, to_xy(f.geometry.coordinates)


def _layer_node_positions(layer: LayerConfig) -> dict[str, tuple[float, float]]:
    if layer.network is None:
        return {}

    feature_points = dict(_iter_feature_points(layer))
    positions: dict[str, tuple[float, float]] = {}
    for node in layer.network.nodes:
        if node.feature_id is None:
            continue
        pos = feature_points.get(node.feature_id)
        if pos is None:
            continue
        positions[node.id] = pos
    return positions


def render_layer_matplotlib(layer: LayerConfig) -> Figure:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon

    if isinstance(layer.domain, AbstractDomainConfig):
        raise NotImplementedError(
            "Matplotlib renderer does not support domain type 'abstract' yet"
        )

    fig, ax = plt.subplots()

    if isinstance(layer.domain, SphereDomainConfig):
        to_xy = _sphere_xy_lat_lon
        ax.set_xlim(-180, 180)
        ax.set_ylim(-90, 90)
        ax.set_xlabel("lon (deg)")
        ax.set_ylabel("lat (deg)")
    else:
        to_xy = _plane_xy
        if isinstance(layer.domain, PlaneDomainConfig) and layer.domain.bounds:
            (xmin, ymin), (xmax, ymax) = layer.domain.bounds
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)

    # Draw features
    for f in layer.features:
        if f.geometry_type == "point":
            x, y = to_xy(f.geometry.coordinates)
            ax.scatter([x], [y], s=20)
        elif f.geometry_type == "path":
            xs, ys = zip(*(to_xy(c) for c in f.geometry.coordinates))
            ax.plot(xs, ys, linewidth=1)
        elif f.geometry_type == "region":
            pts = [to_xy(c) for c in f.geometry.shell]
            poly = Polygon(pts, closed=True, fill=False, linewidth=1)
            ax.add_patch(poly)

    # Overlay network if nodes are placeable (node -> point-feature)
    node_pos = _layer_node_positions(layer)
    if layer.network is not None:
        for e in layer.network.edges:
            p0 = node_pos.get(e.source)
            p1 = node_pos.get(e.target)
            if p0 is None or p1 is None:
                continue
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]], linewidth=0.75, alpha=0.7)

    ax.set_title(layer.id)
    ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    return fig


def render_world_matplotlib(world: WorldConfig) -> list[Figure]:
    return [render_layer_matplotlib(layer) for layer in world.layers]

