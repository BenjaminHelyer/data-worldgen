"""Generate a synthetic US working population using the existing population sampler."""
import argparse
import random
from pathlib import Path

import pandas as pd

from world_builder.population.character import create_characters_vectorized
from world_builder.population.config import load_config

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, default=20000)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--out', type=Path, default=HERE / 'population.parquet')
    args = parser.parse_args()
    if args.count < 1:
        parser.error('--count must be positive')
    # Finite and distribution fields use NumPy; names use Python's random module.
    # Character IDs also contain time/random information and are not reproducible.
    random.seed(args.seed)
    config = load_config(HERE / 'config.json')
    population = create_characters_vectorized(config, args.count, seed=args.seed)
    df = pd.DataFrame([vars(character) for character in population])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out, index=False)
    print(f'Wrote {len(df):,} synthetic characters to {args.out}')


if __name__ == '__main__':
    main()
