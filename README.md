# data-worldgen
Project exploring data technologies using world generation as an example.

## World Builder

Module that creates characters from a specific world.

Has a Pydantic model for the config. Samples static or slowly-changing dimensions related to the character based on a factor-graph approach.

### Get Started Quickly

First, clone the repository then install dependencies:

```
pip install -e .
```

To run the world builder with a config file, use the example script:

```
python examples/world_builder/wb_example.py
```

This uses the config at `examples/world_builder/wb_config.json` and generates 100 characters, saving them to a Parquet file.

To use your own config file, create a Python script:

```python
from pathlib import Path
import pandas as pd
from world_builder import load_config, create_character

CONFIG_FILE = Path("path/to/your/config.json")
config = load_config(CONFIG_FILE)
population = [create_character(config) for _ in range(100)]

population_data = [char.__dict__ for char in population]
df = pd.DataFrame(population_data)
df.to_parquet("population.parquet", index=False)
```

### Population Configuration

The population configuration is a JSON-based system that defines the demographic makeup of a world. It specifies base probabilities for various character attributes (like species, profession, and allegiance), along with a factor-graph approach to model how these attributes influence each other (e.g., how being in a certain city affects the likelihood of different professions). The config also supports distribution-based attributes like age, with the ability to override or transform these distributions based on other character traits.

### Character Generation

The character generation system creates unique individuals by sampling from the population configuration in a structured way. It first samples finite categorical fields (like species and profession), respecting dependencies, then handles distribution-based attributes (like age) with potential overrides based on the character's traits. Each character is assigned a unique character_id identifier and procedurally generated names that match their species and gender.

## Namegen

Generates names using a Markov chain approach based on the data in the United States baby names dataset.

### References
U.S. name analysis taken from https://catalog.data.gov/dataset/baby-names-from-social-security-card-applications-national-data
Wookieepedia for list of Star Wars planets which were used to generate surnames based on planet names
