from __future__ import annotations

import json
from pathlib import Path

import pytest

from spatial_data_generation.reader import load_world_from_path


def test_load_world_from_path_rejects_non_object_json(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps([{"layers": []}]), encoding="utf-8")
    with pytest.raises(ValueError, match="must be a JSON object"):
        load_world_from_path(p)


def test_load_world_from_path_malformed_json_includes_path(tmp_path: Path):
    p = tmp_path / "malformed.json"
    p.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError) as exc_info:
        load_world_from_path(p)
    assert str(p) in str(exc_info.value)

