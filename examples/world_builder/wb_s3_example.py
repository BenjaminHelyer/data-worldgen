from pathlib import Path
import logging
import tempfile
from multiprocessing import Pool, cpu_count
import random
import os
import time
import pandas as pd
import requests
import boto3

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

def get_metadata(path):
    """Fetch metadata from the EC2 metadata service using IMDSv2."""
    try:
        # get the token first to authenticate the metadata request
        token = requests.put(
            "http://169.254.169.254/latest/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
            timeout=2
        ).text
        # now get the actual metadata from the request, using the token
        response = requests.get(
            f"http://169.254.169.254/latest/meta-data/{path}",
            headers={"X-aws-ec2-metadata-token": token},
            timeout=2
        )
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        logger.error(f"Failed to get metadata for {path}: {e}")
        raise


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
    seed = int(time.time() * 1000000) ^ os.getpid()
    random.seed(seed)
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

def terminate_instance():
    """Terminate this EC2 instance via AWS API."""
    try:
        instance_id = get_metadata("instance-id")
        logger.info(f"Instance ID: {instance_id}")
        print(f"Instance ID: {instance_id}")
    except Exception as e:
        logger.error(f"Could not get instance ID: {e}")
        print(f"Could not get instance ID: {e}")
        return

    try:
        try:
            region = get_metadata("placement/region")
        except Exception:
            az = get_metadata("placement/availability-zone")
            region = az[:-1]
        logger.info(f"Region: {region}")
        print(f"Region: {region}")
    except Exception as e:
        logger.error(f"Could not get region: {e}")
        print(f"Could not get region: {e}")
        return

    try:
        ec2 = boto3.client('ec2', region_name=region)
        logger.info(f"EC2 client created")
        print(f"EC2 client created")
    except Exception as e:
        logger.error(f"Could not create EC2 client: {e}")
        print(f"Could not create EC2 client: {e}")
        return

    try:
        logger.info(f"Terminating instance: {instance_id}")
        print(f"Terminating instance: {instance_id}")
        response = ec2.terminate_instances(InstanceIds=[instance_id])
        logger.info(f"Terminate response: {response}")
        print(f"Terminate response: {response}")
    except Exception as e:
        logger.error(f"Failed to terminate instance: {e}")
        print(f"Failed to terminate instance: {e}")

terminate_instance()
