"""
One-shot batch job: download JSON config from S3, generate entities, upload Parquet to S3.

Configure via environment variables and task IAM role for AWS credentials.

Required:
  WORLDGEN_MODE: "ecosystem" or "population"
  Config: CONFIG_S3_URI (s3://bucket/key) or CONFIG_BUCKET + CONFIG_KEY
  Output: OUTPUT_S3_URI or OUTPUT_BUCKET + OUTPUT_KEY

Optional:
  ENTITY_COUNT: number of rows to generate (default 100)
  NUM_WORKERS: multiprocessing pool size cap (default: host CPU count, capped by ENTITY_COUNT)

Chunked Lambda workers (SQS) use run_batch_for_seed_range() with per-index random.seed(i);
see lambda_synthetic_worker.lambda_handler and the event-pipeline PRD.
"""

from __future__ import annotations

import logging
import os
import random
import sys
import tempfile
import time
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

from data_export.s3_upload import download_from_s3, upload_to_s3
from world_builder import (
    create_animal,
    load_config,
    load_ecosystem_config,
)
from world_builder.ecosystem.config import EcosystemConfig
from world_builder.population.character import create_characters_vectorized

logger = logging.getLogger(__name__)


def parse_s3_uri(uri: str) -> Tuple[str, str]:
    """
    Parse s3://bucket/object-key into bucket and key (key may contain '/').
    """
    u = uri.strip()
    if not u.startswith("s3://"):
        raise ValueError(f"Not an s3:// URI: {uri!r}")
    rest = u[5:]
    if "/" not in rest:
        raise ValueError(f"S3 URI must include an object key: {uri!r}")
    bucket, key = rest.split("/", 1)
    if not bucket or not key:
        raise ValueError(f"Invalid S3 URI (empty bucket or key): {uri!r}")
    return bucket, key


def _resolve_location(
    uri_var: str,
    bucket_var: str,
    key_var: str,
    label: str,
) -> Tuple[str, str]:
    uri = os.environ.get(uri_var, "").strip()
    if uri:
        return parse_s3_uri(uri)
    bucket = os.environ.get(bucket_var, "").strip()
    key = os.environ.get(key_var, "").strip()
    if bucket and key:
        return bucket, key
    raise ValueError(
        f"Set {uri_var}=s3://bucket/key or both {bucket_var} and {key_var} for {label}."
    )


def _env_positive_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    value = int(raw)
    if value < 1:
        raise ValueError(f"{name} must be >= 1, got {value}")
    return value


def _effective_worker_count(entity_count: int, requested: int) -> int:
    cpus = max(1, cpu_count())
    return max(1, min(requested, cpus, entity_count))


def _create_animal_worker(_config: EcosystemConfig) -> object:
    seed = int(time.time() * 1_000_000) ^ os.getpid()
    random.seed(seed)
    return create_animal(_config)


def _create_character_at_index(args: tuple[int, PopulationConfig]) -> object:
    idx, cfg = args
    random.seed(idx)
    return create_character(cfg)


def _create_animal_at_index(args: tuple[int, EcosystemConfig]) -> object:
    idx, cfg = args
    random.seed(idx)
    return create_animal(cfg)


def run_seed_range_to_local_parquet(
    mode: str,
    config_path: Path,
    out_path: Path,
    seed_start: int,
    seed_end: int,
    num_workers: Optional[int] = None,
) -> None:
    """
    Generate entities for global indices seed_start..seed_end (inclusive) and write Parquet.
    Same Pool + random.seed(index) path as the Lambda worker. No AWS (except reading
    config_path from disk).

    If num_workers is None, uses NUM_WORKERS from the environment when set, else CPU count.
    """
    mode = mode.strip().lower()
    if mode not in ("ecosystem", "population"):
        raise ValueError(
            'WORLDGEN_MODE must be "ecosystem" or "population", '
            f"got {mode!r}"
        )
    if seed_start < 0 or seed_end < seed_start:
        raise ValueError(
            f"Invalid seed range: seed_start={seed_start} seed_end={seed_end}"
        )

    entity_count = seed_end - seed_start + 1
    default_workers = max(1, cpu_count())
    if num_workers is not None:
        requested_workers = num_workers
    else:
        requested_workers = _env_positive_int("NUM_WORKERS", default_workers)
    workers = _effective_worker_count(entity_count, requested_workers)

    logger.info(
        "Local seed-range batch: mode=%s seeds=[%s,%s] count=%s workers=%s config=%s out=%s",
        mode,
        seed_start,
        seed_end,
        entity_count,
        workers,
        config_path,
        out_path,
    )

    indices = list(range(seed_start, seed_end + 1))
    if mode == "population":
        pop_config = load_config(config_path)
        with Pool(processes=workers) as pool:
            rows = pool.map(
                _create_character_at_index,
                [(i, pop_config) for i in indices],
            )
    else:
        eco_config = load_ecosystem_config(config_path)
        with Pool(processes=workers) as pool:
            rows = pool.map(
                _create_animal_at_index,
                [(i, eco_config) for i in indices],
            )

    data = [r.__dict__ for r in rows]
    df = pd.DataFrame(data)
    logger.info("Built dataframe with shape %s", df.shape)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    logger.info("Wrote %s rows to %s", len(df), out_path)


def run_batch_for_seed_range(
    mode: str,
    config_bucket: str,
    config_key: str,
    output_bucket: str,
    output_key: str,
    seed_start: int,
    seed_end: int,
) -> None:
    """
    Download config from S3, generate seed range, upload Parquet to S3.
    """
    logger.info(
        "Starting chunked batch: mode=%s seeds=[%s,%s] config=s3://%s/%s output=s3://%s/%s",
        mode,
        seed_start,
        seed_end,
        config_bucket,
        config_key,
        output_bucket,
        output_key,
    )

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_cfg:
        config_path = Path(tmp_cfg.name)
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp_out:
        out_path = Path(tmp_out.name)
    try:
        download_from_s3(config_bucket, config_key, str(config_path))
        logger.info("Downloaded config from s3://%s/%s", config_bucket, config_key)
        run_seed_range_to_local_parquet(
            mode,
            config_path,
            out_path,
            seed_start,
            seed_end,
            num_workers=None,
        )
        upload_to_s3(str(out_path), output_bucket, output_key)
        logger.info(
            "Uploaded parquet to s3://%s/%s",
            output_bucket,
            output_key,
        )
    finally:
        config_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)


def run_batch() -> None:
    mode = os.environ.get("WORLDGEN_MODE", "").strip().lower()
    if mode not in ("ecosystem", "population"):
        raise ValueError(
            'WORLDGEN_MODE must be "ecosystem" or "population", '
            f"got {os.environ.get('WORLDGEN_MODE')!r}"
        )

    config_bucket, config_key = _resolve_location(
        "CONFIG_S3_URI", "CONFIG_BUCKET", "CONFIG_KEY", "config input"
    )
    output_bucket, output_key = _resolve_location(
        "OUTPUT_S3_URI", "OUTPUT_BUCKET", "OUTPUT_KEY", "output"
    )

    entity_count = _env_positive_int("ENTITY_COUNT", 100)
    default_workers = max(1, cpu_count())
    requested_workers = _env_positive_int("NUM_WORKERS", default_workers)

    if mode == "population":
        workers_pop = _effective_worker_count(entity_count, requested_workers)
        logger.info(
            "Starting batch: mode=%s entities=%s name_workers=%s config=s3://%s/%s output=s3://%s/%s",
            mode,
            entity_count,
            workers_pop,
            config_bucket,
            config_key,
            output_bucket,
            output_key,
        )
    else:
        workers = _effective_worker_count(entity_count, requested_workers)
        logger.info(
            "Starting batch: mode=%s entities=%s workers=%s config=s3://%s/%s output=s3://%s/%s",
            mode,
            entity_count,
            workers,
            config_bucket,
            config_key,
            output_bucket,
            output_key,
        )

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_cfg:
        config_path = Path(tmp_cfg.name)
    try:
        download_from_s3(config_bucket, config_key, str(config_path))
        logger.info("Downloaded config from s3://%s/%s", config_bucket, config_key)

        if mode == "population":
            pop_config = load_config(config_path)
            seed = int(time.time() * 1_000_000) ^ os.getpid()
            rows = create_characters_vectorized(
                pop_config,
                entity_count,
                seed=seed,
                name_workers=workers_pop,
            )
        else:
            eco_config = load_ecosystem_config(config_path)
            workers = _effective_worker_count(entity_count, requested_workers)
            with Pool(processes=workers) as pool:
                rows = pool.map(_create_animal_worker, [eco_config] * entity_count)

        data = [r.__dict__ for r in rows]
        df = pd.DataFrame(data)
        logger.info("Built dataframe with shape %s", df.shape)

        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp_out:
            out_path = Path(tmp_out.name)
        try:
            df.to_parquet(out_path, index=False)
            upload_to_s3(str(out_path), output_bucket, output_key)
            logger.info(
                "Uploaded parquet to s3://%s/%s",
                output_bucket,
                output_key,
            )
        finally:
            out_path.unlink(missing_ok=True)
    finally:
        config_path.unlink(missing_ok=True)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )
    try:
        run_batch()
    except Exception as exc:
        logger.error("%s", exc, exc_info=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
