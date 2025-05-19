from pathlib import Path
import logging
import tempfile
from multiprocessing import Pool, cpu_count

import pandas as pd

from world_builder import load_config, create_character
from data_export.s3_upload import upload_to_s3, download_from_s3


current_dir = Path(__file__).resolve().parent

CONFIG_FILE = current_dir / "wb_config.json"

# S3 upload settings
BUCKET_NAME = "world-builder-example"
S3_KEY = "population/parquet/population.parquet"

# S3 config settings
S3_CONFIG_KEY = "population/config/wb_config.json"  # Example S3 key for config
USE_S3_CONFIG = True  # Set to True to load config from S3

# default pop size if not specified in S3
POP_SIZE = 100

NUM_CORES = cpu_count()

logging.info(f"Using {NUM_CORES} cores")

# Set up logging to file for CloudWatch Agent
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('/var/log/world-builder/app.log'),
    ]
)
logger = logging.getLogger(__name__)

if USE_S3_CONFIG:
    # Download and load config from S3
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_config_file:
        try:
            download_from_s3(BUCKET_NAME, S3_CONFIG_KEY, tmp_config_file.name)
            logger.info(f"Downloaded config from s3://{BUCKET_NAME}/{S3_CONFIG_KEY} to {tmp_config_file.name}")
            config = load_config(Path(tmp_config_file.name))
        except Exception as e:
            logger.error(f"Failed to download config from S3: {e}")
            raise
    # Download and load POP_SIZE from S3
    S3_POP_SIZE_KEY = "population/config/pop_size.txt"
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_pop_size_file:
        try:
            download_from_s3(BUCKET_NAME, S3_POP_SIZE_KEY, tmp_pop_size_file.name)
            logger.info(f"Downloaded pop size from s3://{BUCKET_NAME}/{S3_POP_SIZE_KEY} to {tmp_pop_size_file.name}")
            with open(tmp_pop_size_file.name, "r") as f:
                POP_SIZE = int(f.read().strip())
        except Exception as e:
            logger.info(f"Failed to download pop size from S3: {e}, using default pop size of {POP_SIZE}")
            # do not raise, just use the default pop size
else:
    config = load_config(CONFIG_FILE)

def _create_character_wrapper(args):
    config = args
    return create_character(config)

# Create argument list (same config object, repeated N times)
args = [config] * POP_SIZE

# Parallel character generation
with Pool(processes=NUM_CORES) as pool:
    population = pool.map(_create_character_wrapper, args)

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
logger.info(f"Parquet file created at {parquet_path}")

# Upload the Parquet file to S3
try:
    upload_to_s3(str(parquet_path), BUCKET_NAME, S3_KEY)
    logger.info(f"Successfully uploaded {parquet_path} to s3://{BUCKET_NAME}/{S3_KEY}")
    print(f"Successfully uploaded {parquet_path} to s3://{BUCKET_NAME}/{S3_KEY}")
except Exception as e:
    logger.error(f"Failed to upload to S3: {e}")
    print(f"Failed to upload to S3: {e}")
