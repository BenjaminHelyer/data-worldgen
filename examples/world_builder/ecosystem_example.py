from pathlib import Path

import pandas as pd

from world_builder import (
    load_ecosystem_config,
    create_animal,
)

current_dir = Path(__file__).resolve().parent

ECOSYSTEM_CONFIG_FILE = current_dir / "ecosystem_config.json"

# Load ecosystem configuration (this will validate probabilities)
ecosystem_config = load_ecosystem_config(ECOSYSTEM_CONFIG_FILE)

# Create a population of 100 random animals
animals = [create_animal(ecosystem_config) for _ in range(1000)]

# Optionally, print some animals
for animal in animals[:5]:
    print(animal)

# Convert each animal to a dictionary.
# If your animal objects are not dict-like, you can customize this conversion.
animals_data = [animal.__dict__ for animal in animals]

# Create a DataFrame from the list of dictionaries
df = pd.DataFrame(animals_data)

print(df.head())

# Write the DataFrame to a Parquet file.
# Make sure you have pyarrow or fastparquet installed (e.g., pip install pyarrow).
df.to_parquet(current_dir / "ecosystem.parquet", index=False)
