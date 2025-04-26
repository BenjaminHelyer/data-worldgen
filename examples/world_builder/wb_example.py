from pathlib import Path

import pandas as pd

from world_builder import load_config, create_character, create_population_dashboard

current_dir = Path(__file__).resolve().parent

CONFIG_FILE = current_dir / "wb_config.json"

# Load configuration (this will validate probabilities)
config = load_config(CONFIG_FILE)

# Create a population of 100 random characters
population = [create_character(config) for _ in range(100)]

# Optionally, print some characters
for char in population[:5]:
    print(char)

# Visualize the population distributions
create_population_dashboard(population, "population.jpg")

# Convert each character to a dictionary.
# If your character objects are not dict-like, you can customize this conversion.
population_data = [char.__dict__ for char in population]

# Create a DataFrame from the list of dictionaries
df = pd.DataFrame(population_data)

print(df.head())

# Write the DataFrame to a Parquet file.
# Make sure you have pyarrow or fastparquet installed (e.g., pip install pyarrow).
df.to_parquet("population.parquet", index=False)
