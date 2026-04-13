from __future__ import annotations

from pathlib import Path
import sys

import matplotlib

from spatial_data_generation import load_world_from_path
from spatial_data_generation.renderers import render_world_matplotlib


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("Usage: python render_example.py path/to/world.json")

    matplotlib.use("Agg")
    world_path = Path(argv[1])
    world = load_world_from_path(world_path)
    figures = render_world_matplotlib(world)

    # Save one image per layer
    for layer, fig in zip(world.layers, figures):
        out = world_path.with_suffix(f".{layer.id}.png")
        fig.savefig(out, dpi=150)
        print(out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

