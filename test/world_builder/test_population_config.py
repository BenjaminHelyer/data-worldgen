from pathlib import Path

import pytest
from pydantic import ValidationError

from world_builder.population_config import load_config

parent_dir = Path(__file__).resolve().parent
CONFIG_DIR = parent_dir / "config"
CONFIG_FILE = CONFIG_DIR / "wb_config_micro.json"


@pytest.mark.parametrize(
    "filename",
    ["wb_config_micro.json"],  # known good config -- should pass
)
def test_load_config_smoke(filename):
    """
    Smoke test: ensure that loading a known good config file works without errors.
    """
    config_path = CONFIG_DIR / filename
    config = load_config(config_path)
    assert config is not None
    assert config.planet is not None
    assert isinstance(config.city_base_probability, dict)


@pytest.mark.parametrize(
    "filename",
    [
        "wb_config_bad_weights_profession.json"
    ],  # intentionally broken config -- profession weights don't sum to 1.0
)
def test_load_config_bad_weights(filename):
    """
    Test that loading a config with invalid weights fails validation.
    """
    config_path = CONFIG_DIR / filename

    with pytest.raises(ValidationError):
        _ = load_config(config_path)
