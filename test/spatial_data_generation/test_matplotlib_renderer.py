from __future__ import annotations

import matplotlib
import pytest

from spatial_data_generation.config_models import LayerConfig
from spatial_data_generation.renderers.matplotlib_renderer import render_layer_matplotlib


def test_render_layer_matplotlib_rejects_abstract_domain():
    matplotlib.use("Agg")
    layer = LayerConfig.model_validate(
        {
            "id": "abs",
            "domain": {"type": "abstract", "metric": "shortest_path"},
            "features": [],
            "network": None,
        }
    )
    with pytest.raises(NotImplementedError, match="abstract"):
        render_layer_matplotlib(layer)

