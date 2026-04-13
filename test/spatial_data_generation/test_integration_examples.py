from __future__ import annotations

from pathlib import Path

import matplotlib

from spatial_data_generation import load_world_from_path
from spatial_data_generation.renderers import render_world_matplotlib


def _config_dir() -> Path:
    return Path(__file__).resolve().parent / "config"


def _use_agg() -> None:
    # Must be set before importing pyplot inside renderers.
    matplotlib.use("Agg")


def test_austin_example_load_validate_render():
    _use_agg()
    world = load_world_from_path(_config_dir() / "small_austin_example.json")
    figures = render_world_matplotlib(world)
    assert len(figures) == 1
    assert all(fig is not None for fig in figures)


def test_milky_way_example_load_validate_render():
    _use_agg()
    world = load_world_from_path(_config_dir() / "small_milky_way_example.json")
    figures = render_world_matplotlib(world)
    assert len(figures) == 1
    assert all(fig is not None for fig in figures)


def test_earth_example_load_validate_render():
    _use_agg()
    world = load_world_from_path(_config_dir() / "small_earth_example.json")
    figures = render_world_matplotlib(world)
    assert len(figures) == 1
    assert all(fig is not None for fig in figures)


def test_medium_example_multi_layer_load_validate_render():
    _use_agg()
    world = load_world_from_path(_config_dir() / "medium_example_galaxy_world.json")
    figures = render_world_matplotlib(world)
    assert len(figures) == len(world.layers)
    assert all(fig is not None for fig in figures)

