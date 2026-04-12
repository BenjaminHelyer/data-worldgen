"""Visualization helpers for layers with domain-specific renderers."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt

from spatial_data_generation.models import DomainKind, GeometryType, Layer


COLORS = {
    "district": "#bfdbfe",
    "city": "#f59e0b",
    "star_system": "#a78bfa",
}


def _draw_plane_layer(ax, layer: Layer, show_network: bool) -> None:
    for feature in layer.features:
        coords = feature.geometry.coordinates
        xs = [p[0] for p in coords]
        ys = [p[1] for p in coords]
        if feature.geometry.type == GeometryType.POINT:
            ax.scatter(xs, ys, s=40, color=COLORS.get(feature.kind, "#111827"))
        elif feature.geometry.type == GeometryType.PATH:
            ax.plot(xs, ys, color="#4b5563", linewidth=1.6)
        else:
            ax.fill(xs, ys, facecolor=COLORS.get(feature.kind, "#cbd5e1"), edgecolor="#1f2937", alpha=0.45)

    if show_network and layer.network:
        pos = {n.id: n.position for n in layer.network.nodes if n.position is not None}
        for edge in layer.network.edges:
            src = pos.get(edge.source)
            dst = pos.get(edge.target)
            if src and dst:
                ax.plot([src[0], dst[0]], [src[1], dst[1]], color="#ef4444", alpha=0.28, linewidth=0.9)

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x")
    ax.set_ylabel("y")


def _draw_sphere_layer(ax, layer: Layer, show_network: bool) -> None:
    # Coordinates are [lat, lon]; convert to radians for Mollweide plot.
    feature_pos: dict[str, tuple[float, float]] = {}
    for feature in layer.features:
        lat, lon = feature.geometry.coordinates[0]
        lon_r = math.radians(lon)
        lat_r = math.radians(lat)
        feature_pos[feature.id] = (lon_r, lat_r)
        ax.scatter(lon_r, lat_r, s=22, alpha=0.85)

    if show_network and layer.network:
        pos = {n.id: (math.radians(n.position[1]), math.radians(n.position[0])) for n in layer.network.nodes if n.position}
        for edge in layer.network.edges:
            src = pos.get(edge.source)
            dst = pos.get(edge.target)
            if src and dst:
                ax.plot([src[0], dst[0]], [src[1], dst[1]], color="#14b8a6", alpha=0.18, linewidth=0.7)

    ax.grid(True, alpha=0.3)
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")


def plot_layer(layer: Layer, show_network: bool = True):
    """Render a layer with an appropriate projection based on domain kind."""
    if layer.domain.kind == DomainKind.SPHERE:
        fig = plt.figure(figsize=(10, 5.5))
        ax = fig.add_subplot(111, projection="mollweide")
        _draw_sphere_layer(ax, layer, show_network)
    else:
        fig, ax = plt.subplots(figsize=(7, 7))
        _draw_plane_layer(ax, layer, show_network)

    ax.set_title(layer.id)
    return fig, ax


def save_layer_plot(layer: Layer, output_path: str, show_network: bool = True) -> None:
    fig, _ = plot_layer(layer, show_network=show_network)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
