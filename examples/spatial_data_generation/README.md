## Spatial data generation examples

These examples exercise the `spatial_data_generation` module (config parsing, validation, and rendering).

### Install

From the repo root:

```bash
pip install -e .
```

### Render example worlds

```bash
python examples/spatial_data_generation/render_example.py examples/spatial_data_generation/galaxy_world_medium.json
python examples/spatial_data_generation/render_example.py examples/spatial_data_generation/austin_small.json
python examples/spatial_data_generation/render_example.py examples/spatial_data_generation/earth_small.json
```

The script writes a PNG next to the input JSON.

