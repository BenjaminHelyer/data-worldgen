"""Generate US workers with the proposal's conditional appearance distributions."""
import argparse
import random
from pathlib import Path

import pandas as pd

from world_builder.core.sampling import sample_finite_fields, sample_distribution_fields_with_overrides
from world_builder.population.character import create_characters_vectorized
from world_builder.population.config import load_config

HERE = Path(__file__).resolve().parent


def add_appearance(character, config):
    """Bind the sampled person's age and species before sampling appearance."""
    fields = {'species': character.species,
              'age_band': 'older_adult' if character.age >= 65 else 'adult'}
    sample_finite_fields(config, fields)
    sample_distribution_fields_with_overrides(config, fields)
    fields['mass_kg'] = round(fields['bmi'] * (fields['stature_cm'] / 100) ** 2, 1)
    return {**vars(character), **fields}


def main():
    from appearance_catalog import load_appearance_catalog_config, add_catalog_appearance
    from occupations import load_occupations, add_occupation
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, default=20000)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--out', type=Path, default=HERE / 'rich_population.parquet')
    args = parser.parse_args()
    if args.count < 1:
        parser.error('--count must be positive')
    random.seed(args.seed)
    people = create_characters_vectorized(load_config(HERE / 'config.json'), args.count, seed=args.seed)
    appearance = load_config(HERE / 'appearance_adult_human.json')
    catalog_appearance = load_appearance_catalog_config()
    occupations = load_occupations()
    rows = []
    for person in people:
        row = add_appearance(person, appearance)
        row = add_catalog_appearance(row, catalog_appearance)
        row.update(add_occupation(row, occupations))
        rows.append(row)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(args.out, index=False)
    print(f'Wrote {len(rows):,} synthetic characters to {args.out}')


if __name__ == '__main__':
    main()
