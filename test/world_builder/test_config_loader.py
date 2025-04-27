from pathlib import Path

from world_builder import load_config

parent_dir = Path(__file__).resolve().parent
CONFIG_DIR = parent_dir / "config"
CONFIG_FILE = CONFIG_DIR / "wb_config_micro.json"


def test_load_config_smoke():
    """
    Tests the load config function on an example config to see if it even runs.
    """
    config = load_config(CONFIG_FILE)
