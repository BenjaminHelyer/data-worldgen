"""Translate selected proposal appearance priors into the existing sampler.

The source catalog contains marginal distributions, not a fully specified joint
model. Dimensions needing rules for hairstyle, clothing or anatomy are omitted.
"""
from collections import defaultdict
from pathlib import Path
import json

from world_builder.core.sampling import sample_finite_fields
from world_builder.population.config import PopulationConfig

SOURCE = Path(__file__).resolve().parent / 'appearance_options.json'
DIMENSIONS = (
    'natural_hair_color', 'hair_texture', 'eye_shape', 'eye_spacing',
    'eyebrow_shape', 'eyebrow_density', 'complexion', 'face_shape',
    'nose_profile', 'lip_shape', 'ear_shape', 'chin_shape',
    'cheekbone_profile', 'posture', 'gait', 'voice_timbre', 'speech_pace',
    'eyewear', 'freckle_density', 'skin_texture',
)


def load_appearance_catalog_config(path=SOURCE):
    """Build a sampler config from adult human marginal and age-based priors."""
    records = json.loads(Path(path).read_text(encoding='utf-8'))['records']
    fields = {name: {} for name in DIMENSIONS}
    factors = defaultdict(dict)
    for row in records:
        dimension = row['dimension']
        if dimension not in fields or 'anatomy:human' not in row['eligible_anatomy_profiles']:
            continue
        if not {'adult', 'older_adult'}.issubset(row['eligible_age_bands']):
            raise ValueError(f'Unexpected eligibility for {row["id"]}')
        fields[dimension][row['value']] = row['probability']
        for rule in row.get('conditional_multipliers', []):
            for age in ('adult', 'older_adult'):
                conditions = rule['when']
                # Conditions outside this population do not affect its weights.
                if all(c['field'] == 'age_band' and
                       ((c['op'] == 'eq' and age == c['value']) or
                        (c['op'] == 'in' and age in c['value'])) for c in conditions):
                    factors[dimension].setdefault(age, {})[row['value']] = rule['multiplier']
    base = {'age_band': {'adult': 0.82, 'older_adult': 0.18}, **fields}
    return PopulationConfig.model_validate({
        'base_probabilities_finite': base,
        'base_probabilities_distributions': {},
        'factors': {'age_band': dict(factors)},
        'override_distributions': [], 'transform_distributions': {},
        'metadata': {'probability_basis': 'synthetic_illustrative'},
    })


def add_catalog_appearance(row, config):
    """Add selected traits while retaining existing sampled identity and fields."""
    result = dict(row)
    sample_finite_fields(config, result)
    if result.get('hair_coverage') == 'bald':
        result['natural_hair_color'] = None
        result['hair_texture'] = None
    return result
