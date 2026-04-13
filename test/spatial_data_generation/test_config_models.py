from __future__ import annotations

import pytest
from pydantic import ValidationError

from spatial_data_generation.config_models import WorldConfig


def test_schema_validation_catches_unknown_domain_type():
    data = {
        "layers": [
            {
                "id": "layer_1",
                "domain": {"type": "cube", "metric": "euclidean"},
                "features": [],
                "network": None,
            }
        ],
        "portals": [],
    }
    with pytest.raises(ValidationError):
        WorldConfig.model_validate(data)

