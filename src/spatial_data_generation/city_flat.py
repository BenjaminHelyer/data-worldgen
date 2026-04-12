"""Backward-compatible city scenario wrappers."""

from spatial_data_generation.scenarios import CitySpec, build_city_layer


def generate_flat_city_layer(layer_id: str, spec: CitySpec):
    """Compat shim; delegates to the abstract scenario builder."""
    return build_city_layer(layer_id, spec)
