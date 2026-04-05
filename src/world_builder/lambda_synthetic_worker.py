"""
AWS Lambda handler for the synthetic-generator worker (SQS event source).

Expects each SQS record body to be JSON from the dispatcher:

  config_bucket, config_key, seed_start, seed_end, chunk_index, total_chunks
  optional: worldgen_mode (else WORLDGEN_MODE env)

Writes Parquet to:
  {OUTPUT_KEY_PREFIX}/{config_stem}/chunk_{chunk_index:04d}.parquet
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from world_builder.batch_s3 import run_batch_for_seed_range

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
        )


def lambda_handler(event: dict, _context: object) -> dict:
    _configure_logging()
    failures = []
    records = event.get("Records") or []
    output_bucket = os.environ.get("OUTPUT_BUCKET", "").strip()
    output_prefix = os.environ.get("OUTPUT_KEY_PREFIX", "outputs/").strip()
    default_mode = os.environ.get("WORLDGEN_MODE", "population").strip()

    if not output_bucket:
        logger.error("OUTPUT_BUCKET is not set")
        return {
            "batchItemFailures": [
                {"itemIdentifier": r["messageId"]} for r in records if r.get("messageId")
            ]
        }

    failures: list[dict] = []

    for record in records:
        mid = record.get("messageId", "")
        try:
            body = json.loads(record["body"])
            config_bucket = body["config_bucket"]
            config_key = body["config_key"]
            seed_start = int(body["seed_start"])
            seed_end = int(body["seed_end"])
            chunk_index = int(body["chunk_index"])
            total_chunks = int(body["total_chunks"])
            mode = str(body.get("worldgen_mode") or default_mode).strip()

            config_stem = Path(config_key).stem
            prefix = output_prefix.rstrip("/")
            output_key = f"{prefix}/{config_stem}/chunk_{chunk_index:04d}.parquet"

            logger.info(
                "Chunk %s/%s seeds=[%s,%s] -> s3://%s/%s",
                chunk_index + 1,
                total_chunks,
                seed_start,
                seed_end,
                output_bucket,
                output_key,
            )

            run_batch_for_seed_range(
                mode=mode,
                config_bucket=config_bucket,
                config_key=config_key,
                output_bucket=output_bucket,
                output_key=output_key,
                seed_start=seed_start,
                seed_end=seed_end,
            )
        except Exception as exc:
            logger.error("Failed message %s: %s", mid, exc, exc_info=True)
            if mid:
                failures.append({"itemIdentifier": mid})

    return {"batchItemFailures": failures}
