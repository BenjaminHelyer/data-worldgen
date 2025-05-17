from pathlib import Path
import pandas as pd
from world_builder import load_config, create_character
from data_export.s3_upload import upload_to_s3

current_dir = Path(__file__).resolve().parent

CONFIG_FILE = current_dir / "wb_config.json"

# S3 upload settings
BUCKET_NAME = "world-builder-example"  # <-- Replace with your S3 bucket name
S3_KEY = "population/parquet/population.parquet"  # <-- S3 object key/path

# Load configuration (this will validate probabilities)
config = load_config(CONFIG_FILE)

# Create a population of 100 random characters
population = [create_character(config) for _ in range(100)]

# Optionally, print some characters
for char in population[:5]:
    print(char)

# Convert each character to a dictionary.
population_data = [char.__dict__ for char in population]

# Create a DataFrame from the list of dictionaries
df = pd.DataFrame(population_data)

print(df.head())

# Write the DataFrame to a Parquet file
parquet_path = current_dir / "population.parquet"
df.to_parquet(parquet_path, index=False)

# Upload the Parquet file to S3
try:
    upload_to_s3(str(parquet_path), BUCKET_NAME, S3_KEY)
    print(f"Successfully uploaded {parquet_path} to s3://{BUCKET_NAME}/{S3_KEY}")
except Exception as e:
    print(f"Failed to upload to S3: {e}")
