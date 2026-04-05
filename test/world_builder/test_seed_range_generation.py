"""
Tier 1: generation logic for seed ranges (no AWS).

Uses the same run_seed_range_to_local_parquet path as the Lambda worker.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from world_builder.batch_s3 import run_seed_range_to_local_parquet

CONFIG_DIR = Path(__file__).resolve().parent / "config"
MICRO_POP = CONFIG_DIR / "wb_config_micro.json"


@pytest.fixture
def micro_population_config() -> Path:
    assert MICRO_POP.is_file(), f"missing fixture config: {MICRO_POP}"
    return MICRO_POP


def test_seed_range_row_count_and_determinism(micro_population_config: Path, tmp_path: Path) -> None:
    """Inclusive range [0, 9] yields 10 rows; two runs match."""
    out1 = tmp_path / "a.parquet"
    out2 = tmp_path / "b.parquet"
    run_seed_range_to_local_parquet(
        "population",
        micro_population_config,
        out1,
        seed_start=0,
        seed_end=9,
        num_workers=2,
    )
    run_seed_range_to_local_parquet(
        "population",
        micro_population_config,
        out2,
        seed_start=0,
        seed_end=9,
        num_workers=2,
    )
    df1 = pd.read_parquet(out1)
    df2 = pd.read_parquet(out2)
    assert len(df1) == 10
    assert df1.shape == df2.shape
    # character_id embeds wall-clock; RNG-driven fields repeat across runs with same seeds
    drop = [c for c in ("character_id",) if c in df1.columns]
    pd.testing.assert_frame_equal(df1.drop(columns=drop), df2.drop(columns=drop))


def test_seed_range_middle_slice_matches_full_indices(micro_population_config: Path, tmp_path: Path) -> None:
    """Rows for [5,7] equal rows 5..7 of a larger [0,9] run (same global seeds)."""
    full_path = tmp_path / "full.parquet"
    slice_path = tmp_path / "slice.parquet"
    run_seed_range_to_local_parquet(
        "population",
        micro_population_config,
        full_path,
        seed_start=0,
        seed_end=9,
        num_workers=2,
    )
    run_seed_range_to_local_parquet(
        "population",
        micro_population_config,
        slice_path,
        seed_start=5,
        seed_end=7,
        num_workers=2,
    )
    full = pd.read_parquet(full_path)
    part = pd.read_parquet(slice_path)
    drop = [c for c in ("character_id",) if c in full.columns]
    pd.testing.assert_frame_equal(
        part.drop(columns=drop).reset_index(drop=True),
        full.iloc[5:8].drop(columns=drop).reset_index(drop=True),
    )


def test_seed_range_invalid_range_raises(micro_population_config: Path, tmp_path: Path) -> None:
    out = tmp_path / "x.parquet"
    with pytest.raises(ValueError, match="Invalid seed range"):
        run_seed_range_to_local_parquet(
            "population",
            micro_population_config,
            out,
            seed_start=5,
            seed_end=3,
            num_workers=1,
        )


def test_seed_range_single_row(micro_population_config: Path, tmp_path: Path) -> None:
    out = tmp_path / "one.parquet"
    run_seed_range_to_local_parquet(
        "population",
        micro_population_config,
        out,
        seed_start=42,
        seed_end=42,
        num_workers=1,
    )
    df = pd.read_parquet(out)
    assert len(df) == 1
