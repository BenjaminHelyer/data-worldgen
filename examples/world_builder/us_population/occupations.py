"""Draw detailed occupation and job attributes from the proposal's illustrative catalog."""
import json
import random
from pathlib import Path

from world_builder.distributions_config import sample_from_config

CATALOG_PATH = Path(__file__).resolve().parent / 'occupation_types.json'

# The basic example uses coarse sectors. These mappings are an example-specific
# interpretation, not an empirical crosswalk. The mixed public/agriculture sector
# is split explicitly so a public-service worker is not assigned a farm job.
SECTORS = {
    'Healthcare': {'health_care'},
    'Education': {'education_care'},
    'Technology': {'technology_engineering'},
    'Manufacturing': {'manufacturing_repair'},
    'Hospitality': {'food_hospitality'},
    'Retail': {'retail_logistics'},
    'Other': {'construction_trades', 'office_finance', 'professional_creative',
              'personal_business_services'},
}
AGRICULTURAL_JOBS = {'Farm equipment operator', 'Crop farm worker',
                     'Livestock caretaker', 'Greenhouse worker', 'Agricultural technician'}


def load_occupations():
    """Read the source catalog once for reuse across generated people."""
    return json.loads(CATALOG_PATH.read_text(encoding='utf-8'))['records']


def candidates_for(profession, records):
    """Find occupations compatible with the basic example's broad profession."""
    if profession in ('Agriculture', 'Public service'):
        mixed = [r for r in records if r['sector'] == 'public_agriculture_services']
        return [r for r in mixed if (r['name'] in AGRICULTURAL_JOBS) == (profession == 'Agriculture')]
    return [r for r in records if r['sector'] in SECTORS.get(profession, set())]


def add_occupation(person, records):
    """Return occupation details sampled conditionally on an existing broad profession.

    The catalog provides wages in minor units/year and does not give actual
    remote-work or night-shift assignments, only probabilities of compatibility.
    Unmapped professions receive null fields instead of invented occupation data.
    """
    matches = candidates_for(person['profession'], records)
    if not matches:
        return {'occupation': None, 'occupation_sector': None,
                'annual_gross_wage_usd_like': None, 'hours_per_week': None,
                'occupation_education_band': None,
                'remote_compatible': None, 'night_shift': None}
    job = random.choices(matches, weights=[r['selection']['probability'] for r in matches], k=1)[0]
    # The catalog's lognormal parameters are arithmetic mean and std in cents.
    wage = sample_from_config(job['annual_gross_wage_prior']['distribution']) / 100
    hours = sample_from_config(job['hours_per_week_prior']['distribution'])
    return {'occupation': job['name'], 'occupation_sector': job['sector'],
            'annual_gross_wage_usd_like': round(max(0, wage), 2),
            'hours_per_week': round(hours, 1),
            'occupation_education_band': job['education_band'],
            'remote_compatible': random.random() < job['remote_compatible_probability'],
            'night_shift': random.random() < job['night_shift_probability']}
