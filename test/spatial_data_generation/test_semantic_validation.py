from __future__ import annotations

from copy import deepcopy

import pytest

from spatial_data_generation import load_world_from_dict
from spatial_data_generation.semantic_validation import SpatialConfigError


def _minimal_plane_world() -> dict:
    return {
        "layers": [
            {
                "id": "layer_1",
                "domain": {
                    "type": "plane",
                    "metric": "euclidean",
                    "bounds": [[0.0, 0.0], [10.0, 10.0]],
                },
                "features": [
                    {
                        "id": "p1",
                        "kind": "poi",
                        "geometry_type": "point",
                        "geometry": {"coordinates": [1.0, 2.0]},
                    }
                ],
                "network": {
                    "nodes": [{"id": "n1", "feature_id": "p1"}],
                    "edges": [],
                },
            }
        ],
        "portals": [],
    }


def test_rejects_duplicate_layer_ids():
    data = _minimal_plane_world()
    data["layers"].append(deepcopy(data["layers"][0]))
    with pytest.raises(SpatialConfigError, match="Duplicate layer ids"):
        load_world_from_dict(data)


def test_rejects_duplicate_feature_ids_within_layer():
    data = _minimal_plane_world()
    dup = deepcopy(data["layers"][0]["features"][0])
    data["layers"][0]["features"].append(dup)
    with pytest.raises(SpatialConfigError, match="Duplicate feature ids"):
        load_world_from_dict(data)


def test_rejects_edge_with_unknown_node():
    data = _minimal_plane_world()
    data["layers"][0]["network"]["edges"].append(
        {
            "id": "e1",
            "source": "n1",
            "target": "missing",
            "directed": False,
            "weights": {"cost": 1.0},
        }
    )
    with pytest.raises(SpatialConfigError, match="unknown target node"):
        load_world_from_dict(data)


def test_rejects_node_with_unknown_feature_id():
    data = _minimal_plane_world()
    data["layers"][0]["network"]["nodes"][0]["feature_id"] = "missing_feature"
    with pytest.raises(SpatialConfigError, match="references unknown feature_id"):
        load_world_from_dict(data)


def test_rejects_plane_bounds_wrong_shape():
    data = _minimal_plane_world()
    data["layers"][0]["domain"]["bounds"] = [[0.0, 0.0]]  # wrong shape
    with pytest.raises(SpatialConfigError, match="bounds"):
        load_world_from_dict(data)


def test_rejects_portal_cycle():
    data = _minimal_plane_world()
    data["layers"].append(
        {
            "id": "layer_2",
            "domain": {"type": "plane", "metric": "euclidean"},
            "features": [
                {
                    "id": "p2",
                    "kind": "poi",
                    "geometry_type": "point",
                    "geometry": {"coordinates": [2.0, 3.0]},
                }
            ],
            "network": None,
        }
    )
    data["portals"] = [
        {
            "id": "p12",
            "source_layer_id": "layer_1",
            "target_layer_id": "layer_2",
            "source_selector": {"feature_id": "p1"},
            "target_selector": {"layer_entry": True},
        },
        {
            "id": "p21",
            "source_layer_id": "layer_2",
            "target_layer_id": "layer_1",
            "source_selector": {"feature_id": "p2"},
            "target_selector": {"layer_entry": True},
        },
    ]
    with pytest.raises(SpatialConfigError, match="cycle"):
        load_world_from_dict(data)


def test_rejects_bad_sphere_lat_lon_ranges():
    data = {
        "layers": [
            {
                "id": "earth",
                "domain": {
                    "type": "sphere",
                    "metric": "geodesic",
                    "radius": 1.0,
                    "coordinate_system": "lat_lon_degrees",
                },
                "features": [
                    {
                        "id": "bad_lat",
                        "kind": "city",
                        "geometry_type": "point",
                        "geometry": {"coordinates": [120.0, 0.0]},
                    }
                ],
                "network": None,
            }
        ],
        "portals": [],
    }
    with pytest.raises(SpatialConfigError, match="invalid latitude"):
        load_world_from_dict(data)

