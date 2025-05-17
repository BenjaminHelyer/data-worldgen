"""
Provides a function for uploading files to an AWS S3 bucket.

This module contains a utility function to upload a local file to an S3 bucket using boto3.
"""

import boto3
from botocore.exceptions import NoCredentialsError, ClientError

def upload_to_s3(local_file_path: str, bucket_name: str, s3_key: str) -> None:
    """
    Upload a local file to an S3 bucket.
    Args:
        local_file_path: Path to the local file to upload.
        bucket_name: Name of the target S3 bucket.
        s3_key: The S3 object key (path in the bucket).
    Raises:
        FileNotFoundError: If the local file does not exist.
        NoCredentialsError: If AWS credentials are not found.
        ClientError: If the upload fails due to AWS error.
    """
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(local_file_path, bucket_name, s3_key)
    except FileNotFoundError:
        raise FileNotFoundError(f"Local file not found: {local_file_path}")
    except NoCredentialsError:
        raise NoCredentialsError("AWS credentials not found.")
    except ClientError as e:
        raise ClientError(e.response, e.operation_name) 
    