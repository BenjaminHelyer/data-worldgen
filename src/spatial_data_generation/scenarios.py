"""Scenario builders that exercise the abstract spatial schema end-to-end."""

from __future__ import annotations

from dataclasses import dataclass
import math

from spatial_data_generation.models import (
    Domain,
    DomainKind,
    Feature,
    Geometry,
    GeometryType,
    Layer,
    Network,
    NetworkEdge,
    NetworkNode,
    Portal,
    World,
)


@dataclass(frozen=True)
class CitySpec:
    width: float = 100.0
    height: float = 80.0
    blocks_x: int = 4
    blocks_y: int = 3


@dataclass(frozen=True)
class PlanetSpec:
    lat_bands: int = 5
    lon_bands: int = 8


@dataclass(frozen=True)
class GalaxySpec:
    systems: int = 7


def _grid_positions(length: float, count: int) -> list[float]:
    if count < 2:
        raise ValueError("grid count must be >= 2")
    step = length / (count - 1)
    return [i * step for i in range(count)]


def build_city_layer(layer_id: str, spec: CitySpec) -> Layer:
    x_lines = _grid_positions(spec.width, spec.blocks_x + 1)
    y_lines = _grid_positions(spec.height, spec.blocks_y + 1)

    features: list[Feature] = []
    for i in range(spec.blocks_x):
        for j in range(spec.blocks_y):
            x0, x1 = x_lines[i], x_lines[i + 1]
            y0, y1 = y_lines[j], y_lines[j + 1]
            features.append(
                Feature(
                    id=f"district_{i}_{j}",
                    kind="district",
                    geometry=Geometry(
                        type=GeometryType.REGION,
                        coordinates=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
                    ),
                    properties={"grid": [i, j]},
                )
            )

    nodes: list[NetworkNode] = []
    edges: list[NetworkEdge] = []
    node_id_by_grid: dict[tuple[int, int], str] = {}

    for i, x in enumerate(x_lines):
        for j, y in enumerate(y_lines):
            nid = f"cross_{i}_{j}"
            node_id_by_grid[(i, j)] = nid
            nodes.append(NetworkNode(id=nid, position=[x, y]))

    for i in range(len(x_lines)):
        for j in range(len(y_lines)):
            if i + 1 < len(x_lines):
                a = node_id_by_grid[(i, j)]
                b = node_id_by_grid[(i + 1, j)]
                c = x_lines[i + 1] - x_lines[i]
                edges.extend([NetworkEdge(source=a, target=b, cost=c), NetworkEdge(source=b, target=a, cost=c)])
            if j + 1 < len(y_lines):
                a = node_id_by_grid[(i, j)]
                b = node_id_by_grid[(i, j + 1)]
                c = y_lines[j + 1] - y_lines[j]
                edges.extend([NetworkEdge(source=a, target=b, cost=c), NetworkEdge(source=b, target=a, cost=c)])

    return Layer(
        id=layer_id,
        domain=Domain(
            kind=DomainKind.PLANE,
            metric="euclidean",
            dimension=2,
            bounds={"min": [0.0, 0.0], "max": [spec.width, spec.height]},
        ),
        features=features,
        network=Network(nodes=nodes, edges=edges, directed=True),
    )


def build_planet_layer(layer_id: str, spec: PlanetSpec) -> Layer:
    latitudes = [(-60 + 120 * i / (spec.lat_bands - 1)) for i in range(spec.lat_bands)]
    longitudes = [(-180 + 360 * j / spec.lon_bands) for j in range(spec.lon_bands)]

    features: list[Feature] = []
    nodes: list[NetworkNode] = []
    edges: list[NetworkEdge] = []

    for i, lat in enumerate(latitudes):
        for j, lon in enumerate(longitudes):
            city_id = f"city_{i}_{j}"
            features.append(
                Feature(
                    id=city_id,
                    kind="city",
                    geometry=Geometry(type=GeometryType.POINT, coordinates=[[lat, lon]]),
                    properties={"population_m": round(0.5 + ((i + j) % 5) * 0.7, 2)},
                )
            )
            nodes.append(NetworkNode(id=city_id, position=[lat, lon]))

    for i in range(spec.lat_bands):
        for j in range(spec.lon_bands):
            curr = f"city_{i}_{j}"
            east = f"city_{i}_{(j + 1) % spec.lon_bands}"
            if i + 1 < spec.lat_bands:
                north = f"city_{i + 1}_{j}"
                edges.append(NetworkEdge(source=curr, target=north, cost=1.0))
                edges.append(NetworkEdge(source=north, target=curr, cost=1.0))
            edges.append(NetworkEdge(source=curr, target=east, cost=1.0))
            edges.append(NetworkEdge(source=east, target=curr, cost=1.0))

    return Layer(
        id=layer_id,
        domain=Domain(kind=DomainKind.SPHERE, metric="geodesic", dimension=2),
        features=features,
        network=Network(nodes=nodes, edges=edges, directed=True),
    )


def build_galaxy_layer(layer_id: str, spec: GalaxySpec) -> Layer:
    radius = 90.0
    systems = []
    for idx in range(spec.systems):
        theta = (2 * math.pi * idx) / spec.systems
        x = radius * math.cos(theta)
        y = radius * math.sin(theta)
        systems.append((idx, x, y))

    features: list[Feature] = []
    nodes: list[NetworkNode] = []
    edges: list[NetworkEdge] = []
    for idx, x, y in systems:
        sid = f"system_{idx}"
        features.append(
            Feature(
                id=sid,
                kind="star_system",
                geometry=Geometry(type=GeometryType.POINT, coordinates=[[x, y]]),
            )
        )
        nodes.append(NetworkNode(id=sid, position=[x, y]))

    for idx in range(spec.systems):
        a = f"system_{idx}"
        b = f"system_{(idx + 1) % spec.systems}"
        c = f"system_{(idx + 2) % spec.systems}"
        edges.append(NetworkEdge(source=a, target=b, cost=1.0, properties={"kind": "ring"}))
        edges.append(NetworkEdge(source=a, target=c, cost=1.7, properties={"kind": "chord"}))

    return Layer(
        id=layer_id,
        domain=Domain(
            kind=DomainKind.PLANE,
            metric="euclidean",
            dimension=2,
            bounds={"min": [-100.0, -100.0], "max": [100.0, 100.0]},
        ),
        features=features,
        network=Network(nodes=nodes, edges=edges, directed=True),
    )


def build_reference_world() -> World:
    galaxy = build_galaxy_layer("galaxy", GalaxySpec())
    planet = build_planet_layer("planet_0", PlanetSpec())
    city = build_city_layer("city_0_0", CitySpec())

    return World(
        layers=[galaxy, planet, city],
        portals=[
            Portal(
                id="portal_system_to_planet",
                source_layer_id="galaxy",
                target_layer_id="planet_0",
                source_feature_id="system_0",
            ),
            Portal(
                id="portal_planet_city",
                source_layer_id="planet_0",
                target_layer_id="city_0_0",
                source_feature_id="city_0_0",
            ),
        ],
    )
