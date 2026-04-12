import pytest
from pydantic import ValidationError

from spatial_data_generation.models import (
    Domain,
    DomainKind,
    Feature,
    Geometry,
    GeometryType,
    Layer,
    Portal,
    World,
)
from spatial_data_generation.scenarios import (
    CitySpec,
    GalaxySpec,
    PlanetSpec,
    build_city_layer,
    build_galaxy_layer,
    build_planet_layer,
    build_reference_world,
)


def test_plane_bounds_validate_vector_shape():
    with pytest.raises(ValidationError):
        Domain(
            kind=DomainKind.PLANE,
            metric="euclidean",
            dimension=2,
            bounds={"min": [0.0], "max": [1.0, 1.0]},
        )


def test_layer_enforces_embedding_dimension():
    with pytest.raises(ValidationError):
        Layer(
            id="bad",
            domain=Domain(kind=DomainKind.PLANE, metric="euclidean", dimension=2),
            features=[
                Feature(
                    id="f0",
                    kind="poi",
                    geometry=Geometry(type=GeometryType.POINT, coordinates=[[1.0, 2.0, 3.0]]),
                )
            ],
        )


def test_world_portal_hierarchy_must_be_acyclic():
    a = build_city_layer("a", CitySpec())
    b = build_city_layer("b", CitySpec())
    with pytest.raises(ValidationError):
        World(
            layers=[a, b],
            portals=[
                Portal(id="p1", source_layer_id="a", target_layer_id="b"),
                Portal(id="p2", source_layer_id="b", target_layer_id="a"),
            ],
        )


def test_multiscale_reference_world_e2e():
    world = build_reference_world()

    assert len(world.layers) == 3
    assert len(world.portals) == 2

    galaxy = next(layer for layer in world.layers if layer.id == "galaxy")
    planet = next(layer for layer in world.layers if layer.id == "planet_0")
    city = next(layer for layer in world.layers if layer.id == "city_0_0")

    assert galaxy.domain.kind == DomainKind.PLANE
    assert planet.domain.kind == DomainKind.SPHERE
    assert city.domain.kind == DomainKind.PLANE

    assert galaxy.network is not None and len(galaxy.network.nodes) == GalaxySpec().systems
    assert planet.network is not None and len(planet.network.nodes) == PlanetSpec().lat_bands * PlanetSpec().lon_bands

    expected_city_nodes = (CitySpec().blocks_x + 1) * (CitySpec().blocks_y + 1)
    assert city.network is not None and len(city.network.nodes) == expected_city_nodes


def test_sphere_requires_geodesic_metric():
    with pytest.raises(ValidationError):
        Domain(kind=DomainKind.SPHERE, metric="euclidean", dimension=2)


def test_scenario_builders_construct_valid_layers():
    assert build_galaxy_layer("g", GalaxySpec()).id == "g"
    assert build_planet_layer("p", PlanetSpec()).id == "p"
