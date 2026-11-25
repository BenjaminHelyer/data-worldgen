"""Check the catalog crosswalk and conditional occupation generation."""
import importlib.util
from pathlib import Path
import random

PATH = Path(__file__).resolve().parents[2] / 'examples/world_builder/us_population/occupations.py'
SPEC = importlib.util.spec_from_file_location('us_occupations', PATH)
occupations = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(occupations)


def test_catalog_crosswalk_and_generation():
    records = occupations.load_occupations()
    assert len(records) == 165
    for name in ['Healthcare', 'Education', 'Technology', 'Agriculture',
                 'Manufacturing', 'Hospitality', 'Retail', 'Public service', 'Other']:
        assert occupations.candidates_for(name, records)
    assert not occupations.candidates_for('Energy', records)
    assert all(r['name'] in occupations.AGRICULTURAL_JOBS
               for r in occupations.candidates_for('Agriculture', records))
    assert all(r['name'] not in occupations.AGRICULTURAL_JOBS
               for r in occupations.candidates_for('Public service', records))
    random.seed(77)
    sample = occupations.add_occupation({'profession': 'Healthcare'}, records)
    assert sample['occupation_sector'] == 'health_care'
    assert sample['annual_gross_wage_usd_like'] > 0
    assert 8 <= sample['hours_per_week'] <= 65
    random.seed(77)
    assert sample == occupations.add_occupation({'profession': 'Healthcare'}, records)
    assert occupations.add_occupation({'profession': 'Energy'}, records)['occupation'] is None
