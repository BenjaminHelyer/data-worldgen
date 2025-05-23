from pathlib import Path
import logging
import time
from multiprocessing import Pool, cpu_count
import os

import pandas as pd
import boto3
import requests

from world_builder import load_config, create_character
from data_export.s3_upload import upload_to_s3

# Set up logging to file for CloudWatch Agent
try:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler("/var/log/world-builder/app.log"),
        ],
    )
    logger = logging.getLogger(__name__)
except:  # use default logging if not running in EC2
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logger = logging.getLogger(__name__)


def get_metadata(path):
    """Fetch metadata from the EC2 metadata service using IMDSv2."""
    try:
        # get the token first to authenticate the metadata request
        token = requests.put(
            "http://169.254.169.254/latest/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
            timeout=2,
        ).text
        # now get the actual metadata from the request, using the token
        response = requests.get(
            f"http://169.254.169.254/latest/meta-data/{path}",
            headers={"X-aws-ec2-metadata-token": token},
            timeout=2,
        )
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        logger.error(f"Failed to get metadata for {path}: {e}")
        raise


current_dir = Path(__file__).resolve().parent
CONFIG_FILE = current_dir / "wb_config.json"

NUM_CORES = cpu_count()
logger.info(f"Number of cores: {NUM_CORES}")
print(f"Number of cores: {NUM_CORES}")

# Population sizes to benchmark
POP_SIZES = [100, 1000, 10000]
# Number of rounds to run
ROUND_COUNTS = list(range(1, 6))

# Load configuration (this will validate probabilities)
config = load_config(CONFIG_FILE)

# Fetch instance type using metadata
try:
    instance_type = get_metadata("instance-type")
    logger.info(f"Instance type: {instance_type}")
    print(f"Instance type: {instance_type}")
except Exception as e:
    logger.error(f"Could not get instance type: {e}")
    print(f"Could not get instance type: {e}")
    instance_type = "unknown"

# S3 upload settings
BUCKET_NAME = "world-builder-example"  # <-- Replace with your S3 bucket name
S3_KEY = f"population/benchmark/benchmark_{instance_type}.csv"  # <-- S3 object key/path with instance type


def create_character_wrapper(_):
    # Wrapper to allow Pool.map to call create_character with config
    return create_character(config)


results = []

for round_num in ROUND_COUNTS:
    for pop_size in POP_SIZES:
        start_time = time.time()
        num_proc = NUM_CORES
        with Pool(processes=num_proc) as pool:
            # we don't care about memory here -- in fact, we want to be independent of it for these benchmarks
            # Use imap() instead of map() to process one at a time
            # Immediately discard each result after processing
            for _ in pool.imap(create_character_wrapper, range(pop_size)):
                pass
        elapsed = time.time() - start_time
        print(
            f"Round: {round_num}, Population size: {pop_size}, Processes: {num_proc}, Time taken: {elapsed:.2f} seconds"
        )
        logger.info(
            f"Round: {round_num}, Population size: {pop_size}, Processes: {num_proc}, Time taken: {elapsed:.2f} seconds"
        )
        results.append(
            {
                "round_num": round_num,
                "population_size": pop_size,
                "num_processes": num_proc,
                "time_seconds": elapsed,
                "instance_type": instance_type,
            }
        )

# Write benchmark results to CSV
results_df = pd.DataFrame(results)
csv_path = current_dir / "wb_benchmark_results.csv"
results_df.to_csv(csv_path, index=False)
print(f"Benchmark results written to {csv_path}")

# Upload the csv file to S3
try:
    upload_to_s3(str(csv_path), BUCKET_NAME, S3_KEY)
    logger.info(f"Successfully uploaded {csv_path} to s3://{BUCKET_NAME}/{S3_KEY}")
    print(f"Successfully uploaded {csv_path} to s3://{BUCKET_NAME}/{S3_KEY}")
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
        ec2 = boto3.client("ec2", region_name=region)
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


# At the very end of the script, after all processing and logging:
terminate_instance()
