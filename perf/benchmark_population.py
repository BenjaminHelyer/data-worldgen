"""
Population generation benchmarks using the same JSON configs as test/world_builder/config.

Times end-to-end local batch generation (vectorized sampling, pooled name assignment,
DataFrame build, Parquet write), matching world_builder.batch_local.run_local.

Usage (from repository root):

  PYTHONPATH=src python perf/benchmark_population.py

Or with an editable install (pip install -e .), PYTHONPATH is not required.
"""

from __future__ import annotations

import argparse
import io
import statistics
import sys
import time
from multiprocessing import cpu_count
from pathlib import Path
from tempfile import TemporaryDirectory

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Importing world_builder pulls Streamlit dashboards; silence their stderr spam here only.
_err = sys.stderr
sys.stderr = io.StringIO()
try:
    from world_builder.batch_local import run_local  # noqa: E402
finally:
    sys.stderr = _err

_CONFIG_DIR = _REPO_ROOT / "test" / "world_builder" / "config"

_DEFAULT_CONFIGS: dict[str, Path] = {
    "small": _CONFIG_DIR / "wb_config_small.json",
    "medium": _CONFIG_DIR / "wb_config_medium.json",
    "large": _CONFIG_DIR / "wb_config_large.json",
}


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Benchmark population generation with test suite configs."
    )
    p.add_argument(
        "--count",
        type=int,
        default=100_000,
        help="Number of characters per run (default: 100000)",
    )
    p.add_argument(
        "--runs",
        type=int,
        default=5,
        help="Repeated runs per config (default: 5)",
    )
    p.add_argument(
        "--workers",
        type=int,
        default=max(1, cpu_count()),
        help="Multiprocessing pool size cap (default: CPU count)",
    )
    return p.parse_args()


def _benchmark_config(
    label: str,
    config_path: Path,
    entity_count: int,
    num_runs: int,
    workers: int,
) -> list[float]:
    if not config_path.is_file():
        raise FileNotFoundError(f"Config not found: {config_path}")

    times_s: list[float] = []
    for i in range(num_runs):
        with TemporaryDirectory() as td:
            out = Path(td) / "bench.parquet"
            t0 = time.perf_counter()
            run_local("population", config_path, out, entity_count, workers)
            elapsed = time.perf_counter() - t0
        times_s.append(elapsed)
        print(f"  {label} run {i + 1}/{num_runs}: {elapsed:.3f}s", flush=True)
    return times_s


def main() -> int:
    args = _parse_args()
    if args.count < 1:
        print("error: --count must be >= 1", file=sys.stderr)
        return 1
    if args.runs < 1:
        print("error: --runs must be >= 1", file=sys.stderr)
        return 1
    if args.workers < 1:
        print("error: --workers must be >= 1", file=sys.stderr)
        return 1

    print(
        f"Benchmark: population mode, {args.count} characters, "
        f"{args.runs} runs per config, workers_cap={args.workers}\n",
        flush=True,
    )

    for label, path in sorted(_DEFAULT_CONFIGS.items()):
        print(f"Config: {label} ({path.name})", flush=True)
        times_s = _benchmark_config(label, path, args.count, args.runs, args.workers)
        mean = statistics.mean(times_s)
        stdev = statistics.stdev(times_s) if len(times_s) > 1 else 0.0
        per_sec = args.count / mean
        print(
            f"  summary: mean={mean:.3f}s  stdev={stdev:.3f}s  "
            f"~{per_sec:,.0f} characters/s\n",
            flush=True,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
