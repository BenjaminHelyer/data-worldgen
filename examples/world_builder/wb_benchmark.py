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

current_dir = Path(__file__).resolve().parent
CONFIG_FILE = current_dir / "wb_config.json"

# Population sizes to benchmark
POP_SIZES = [100, 1000]
# Number of processes to benchmark
PROCESS_COUNTS = list(range(1, 9))
# Number of rounds to run
ROUND_COUNTS = list(range(1, 3))

# Load configuration (this will validate probabilities)
config = load_config(CONFIG_FILE)

# S3 upload settings
BUCKET_NAME = "world-builder-example"  # <-- Replace with your S3 bucket name
S3_KEY = "population/parquet/benchmark.csv"  # <-- S3 object key/path

# Set up logging to file for CloudWatch Agent
try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler('/var/log/world-builder/app.log'),
        ]
    )
    logger = logging.getLogger(__name__)
except: # use default logging if not running in EC2
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
    )
    logger = logging.getLogger(__name__)

def create_character_wrapper(_):
    # Wrapper to allow Pool.map to call create_character with config
    return create_character(config)

results = []

for round_num in ROUND_COUNTS:
    for pop_size in POP_SIZES:
        for num_proc in PROCESS_COUNTS:
            start_time = time.time()
            with Pool(processes=num_proc) as pool:
                population = pool.map(create_character_wrapper, range(pop_size))
            population_data = [char.__dict__ for char in population]
            df = pd.DataFrame(population_data)
            # parquet_path = current_dir / f"population_{pop_size}_proc{num_proc}.parquet"
            # df.to_parquet(parquet_path, index=False)
            elapsed = time.time() - start_time
            print(f"Round: {round_num}, Population size: {pop_size}, Processes: {num_proc}, Time taken: {elapsed:.2f} seconds")
            results.append({
                "round_num": round_num,
                "population_size": pop_size,
                "num_processes": num_proc,
                "time_seconds": elapsed
            })

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
    # Query the AWS EC2 instance metadata service to get this instance's unique ID.
    # 169.254.169.254 is a special IP only accessible from within the instance.
    # The /latest/meta-data/instance-id path returns the instance's ID as a string.
    try:
        instance_id = requests.get('http://169.254.169.254/latest/meta-data/instance-id', timeout=2).text
        logger.info(f"Instance ID: {instance_id}")
        print(f"Instance ID: {instance_id}")
    except Exception as e:
        logger.error(f"Could not get instance ID: {e}")
        print(f"Could not get instance ID: {e}")
        return

    # Set your region here if different
    region = 'us-east-1'  # <-- Change to your instance's region if needed
    ec2 = boto3.client('ec2', region_name=region)

    try:
        response = ec2.terminate_instances(InstanceIds=[instance_id])
        logger.info(f"Terminate response: {response}")
        print(f"Terminate response: {response}")
    except Exception as e:
        logger.error(f"Failed to terminate instance: {e}")
        print(f"Failed to terminate instance: {e}")

# At the very end of the script, after all processing and logging:
terminate_instance()