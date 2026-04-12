"""Build a reference multiscale world and render each layer."""

from spatial_data_generation.scenarios import build_reference_world
from spatial_data_generation.visualize import save_layer_plot


if __name__ == "__main__":
    world = build_reference_world()

    for layer in world.layers:
        out = f"{layer.id}.png"
        save_layer_plot(layer, out, show_network=True)
        print(f"saved {out}")

    print(f"layers={len(world.layers)} portals={len(world.portals)}")
