"""Check that appearance is conditioned on the existing person's age."""
import importlib.util
import random
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / 'examples/world_builder/us_population/generate_rich.py'
spec = importlib.util.spec_from_file_location('us_rich', PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_appearance_binds_age_and_preserves_person():
    config = module.load_config(module.HERE / 'appearance_adult_human.json')
    random.seed(42)
    younger = module.add_appearance(SimpleNamespace(species='human', age=64, character_id='a'), config)
    older = module.add_appearance(SimpleNamespace(species='human', age=65, character_id='b'), config)
    assert younger['age_band'] == 'adult'
    assert older['age_band'] == 'older_adult'
    assert older['character_id'] == 'b'
    assert 138 <= older['stature_cm'] <= 202
    assert older['mass_kg'] == round(older['bmi'] * (older['stature_cm'] / 100) ** 2, 1)
    assert older['eye_color'] in config.base_probabilities_finite['eye_color']
