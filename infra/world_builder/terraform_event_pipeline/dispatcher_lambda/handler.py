"""
Dispatcher Lambda: SNS (S3 event) -> read config -> enqueue chunked SQS jobs.
"""

from __future__ import annotations

import json
import logging
import math
import os
import urllib.parse

import boto3

logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _s3_client():
    return boto3.client("s3")


def _sqs_client():
    return boto3.client("sqs")


def _entity_count(cfg: dict, fallback: int) -> int:
    for key in ("entity_count", "ENTITY_COUNT", "entityCount"):
        if key in cfg and cfg[key] is not None:
            return max(1, int(cfg[key]))
    return max(1, fallback)


def _worldgen_mode(cfg: dict, fallback: str) -> str:
    v = cfg.get("worldgen_mode") or cfg.get("WORLDGEN_MODE") or fallback
    return str(v).strip().lower()


def chunk_job_bodies(
    *,
    config_bucket: str,
    config_key: str,
    total: int,
    seeds_per_chunk: int,
    worldgen_mode: str,
) -> list[dict]:
    """
    Build SQS message bodies (parsed dicts) for seed partitioning. Pure logic for tests.
    """
    if total < 1:
        raise ValueError("total must be >= 1")
    if seeds_per_chunk < 1:
        raise ValueError("seeds_per_chunk must be >= 1")
    mode = worldgen_mode.strip().lower()
    if mode not in ("ecosystem", "population"):
        raise ValueError(f"invalid worldgen_mode: {worldgen_mode!r}")

    num_chunks = math.ceil(total / seeds_per_chunk)
    bodies: list[dict] = []
    for chunk_index in range(num_chunks):
        seed_start = chunk_index * seeds_per_chunk
        seed_end = min(total - 1, seed_start + seeds_per_chunk - 1)
        bodies.append(
            {
                "config_bucket": config_bucket,
                "config_key": config_key,
                "seed_start": seed_start,
                "seed_end": seed_end,
                "chunk_index": chunk_index,
                "total_chunks": num_chunks,
                "worldgen_mode": mode,
            }
        )
    return bodies


def _dispatch_one_object(
    bucket: str,
    key: str,
    queue_url: str,
    seeds_per_chunk: int,
    default_entity: int,
    default_mode: str,
) -> None:
    obj = _s3_client().get_object(Bucket=bucket, Key=key)
    raw = json.loads(obj["Body"].read())
    total = _entity_count(raw, default_entity)
    mode = _worldgen_mode(raw, default_mode)
    if mode not in ("ecosystem", "population"):
        mode = default_mode

    bodies = chunk_job_bodies(
        config_bucket=bucket,
        config_key=key,
        total=total,
        seeds_per_chunk=seeds_per_chunk,
        worldgen_mode=mode,
    )
    num_chunks = len(bodies)
    logger.info(
        "Dispatching config=s3://%s/%s total_entities=%s seeds_per_chunk=%s num_chunks=%s",
        bucket,
        key,
        total,
        seeds_per_chunk,
        num_chunks,
    )

    sqs = _sqs_client()
    batch: list[dict] = []
    for chunk_index, body in enumerate(bodies):
        batch.append(
            {
                "Id": f"c{chunk_index}"[:80],
                "MessageBody": json.dumps(body),
            }
        )
        if len(batch) >= 10:
            sqs.send_message_batch(QueueUrl=queue_url, Entries=batch)
            batch = []
    if batch:
        sqs.send_message_batch(QueueUrl=queue_url, Entries=batch)

    logger.info("Finished dispatching %s chunks for s3://%s/%s", num_chunks, bucket, key)


def handler(event: dict, context: object) -> dict:
    queue_url = os.environ["JOB_QUEUE_URL"]
    seeds_per_chunk = int(os.environ.get("SEEDS_PER_CHUNK", "25000"))
    default_entity = int(os.environ.get("DEFAULT_ENTITY_COUNT", "100"))
    default_mode = os.environ.get("DEFAULT_WORLDGEN_MODE", "population").strip()

    for record in event.get("Records", []):
        sns = record.get("Sns") or {}
        inner = json.loads(sns["Message"])
        s3_records = inner.get("Records") or [inner]
        for s3rec in s3_records:
            if "s3" not in s3rec:
                continue
            bucket = s3rec["s3"]["bucket"]["name"]
            key = urllib.parse.unquote_plus(
                s3rec["s3"]["object"]["key"].replace("+", " ")
            )
            _dispatch_one_object(
                bucket,
                key,
                queue_url,
                seeds_per_chunk,
                default_entity,
                default_mode,
            )

    return {}
