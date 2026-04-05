"""
Local batch: read JSON config from disk, generate entities, write Parquet.

No S3; kept separate from world_builder.batch_s3 so either entrypoint can evolve
independently. Population mode uses vectorized sampling plus a process pool for
name/ID assignment; ecosystem mode uses a pool for full entity creation.

Example:
  python -m world_builder.batch_local --mode ecosystem \\
    --config /data/ecosystem_config.json --out /data/out.parquet --count 1000
"""

from __future__ import annotations

import argparse
import logging
import os
import random
import sys
import time
from multiprocessing import Pool, cpu_count
from pathlib import Path

import pandas as pd

from world_builder import (
    create_animal,
    load_config,
    load_ecosystem_config,
)
from world_builder.ecosystem.config import EcosystemConfig
from world_builder.population.character import create_characters_vectorized

logger = logging.getLogger(__name__)


def _effective_worker_count(entity_count: int, requested: int) -> int:
    cpus = max(1, cpu_count())
    return max(1, min(requested, cpus, entity_count))


def _create_animal_worker(_config: EcosystemConfig) -> object:
    seed = int(time.time() * 1_000_000) ^ os.getpid()
    random.seed(seed)
    return create_animal(_config)


def run_local(
    mode: str,
    config_path: Path,
    out_path: Path,
    entity_count: int,
    workers: int,
) -> None:
    if mode == "population":
        workers_eff = _effective_worker_count(entity_count, workers)
        logger.info(
            "Local batch: mode=%s count=%s name_workers=%s config=%s out=%s (vectorized)",
            mode,
            entity_count,
            workers_eff,
            config_path,
            out_path,
        )
        cfg = load_config(config_path)
        seed = int(time.time() * 1_000_000) ^ os.getpid()
        rows = create_characters_vectorized(
            cfg, entity_count, seed=seed, name_workers=workers_eff
        )
    else:
        workers_eff = _effective_worker_count(entity_count, workers)
        logger.info(
            "Local batch: mode=%s count=%s workers=%s config=%s out=%s",
            mode,
            entity_count,
            workers_eff,
            config_path,
            out_path,
        )
        cfg = load_ecosystem_config(config_path)
        with Pool(processes=workers_eff) as pool:
            rows = pool.map(_create_animal_worker, [cfg] * entity_count)
    df = pd.DataFrame([r.__dict__ for r in rows])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    logger.info("Wrote %s rows to %s", len(df), out_path)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )
    parser = argparse.ArgumentParser(description="Batch generate to local Parquet (no S3).")
    parser.add_argument("--mode", choices=("ecosystem", "population"), required=True)
    parser.add_argument("--config", type=Path, required=True, help="Path to JSON config file")
    parser.add_argument("--out", type=Path, required=True, help="Output Parquet path")
    parser.add_argument("--count", type=int, default=100, help="Number of entities (default 100)")
    parser.add_argument(
        "--workers",
        type=int,
        default=max(1, cpu_count()),
        help="Multiprocessing pool size cap (default: CPU count)",
    )
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be >= 1")
    if args.workers < 1:
        parser.error("--workers must be >= 1")
    if not args.config.is_file():
        logger.error("Config file not found: %s", args.config)
        return 1
    try:
        run_local(
            args.mode,
            args.config,
            args.out,
            args.count,
            args.workers,
        )
    except Exception as exc:
        logger.error("%s", exc, exc_info=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
