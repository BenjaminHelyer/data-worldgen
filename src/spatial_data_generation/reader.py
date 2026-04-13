from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from spatial_data_generation.config_models import WorldConfig
from spatial_data_generation.semantic_validation import validate_world


def load_world_from_dict(data: dict[str, Any]) -> WorldConfig:
    world = WorldConfig.model_validate(data)
    validate_world(world)
    return world


def load_world_from_path(path: str | Path) -> WorldConfig:
    p = Path(path)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in '{p}': {e.msg}") from e
    if not isinstance(raw, dict):
        raise ValueError(f"World config must be a JSON object, got {type(raw).__name__}")
    return load_world_from_dict(raw)

