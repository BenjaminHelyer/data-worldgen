"""Generate and plot a sample flat city layer."""

from spatial_data_generation.city_flat import CitySpec, generate_flat_city_layer
from spatial_data_generation.visualize import save_layer_plot


def main() -> None:
    city = generate_flat_city_layer("city_alpha", CitySpec(width=120, height=80, blocks_x=6, blocks_y=4))
    save_layer_plot(city, "city_alpha.png", show_network=True)
    print(
        f"Generated layer '{city.id}' with {len(city.features)} features, "
        f"{len(city.network.nodes)} nodes, and {len(city.network.edges)} edges."
    )


if __name__ == "__main__":
    main()
