"""Check catalog translation and age-conditioned appearance sampling."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    'appearance_catalog', ROOT / 'examples/world_builder/us_population/appearance_catalog.py'
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_catalog_config_and_existing_attributes():
    config = module.load_appearance_catalog_config()
    assert config.base_probabilities_finite['natural_hair_color']['black'] == 0.26
    assert config.factors['age_band']['natural_hair_color']['older_adult']['black'] == 0.5
    person = {'age_band': 'older_adult', 'hair_coverage': 'bald', 'eye_color': 'blue'}
    result = module.add_catalog_appearance(person, config)
    assert result['eye_color'] == 'blue'
    assert result['hair_coverage'] == 'bald'
    assert result['natural_hair_color'] is None
    assert result['hair_texture'] is None
    assert result['face_shape'] in config.base_probabilities_finite['face_shape']
