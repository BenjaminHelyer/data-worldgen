# Performance changes in version 0.4.0

This document summarizes **namegen and population batch** improvements in **data-worldgen 0.4.0**. Markov preprocessing and `bisect` sampling from 0.3.0 are unchanged; 0.4.0 removes redundant work on the path from config load to first-name generation.

## Measured impact (local batch benchmark)

End-to-end timing from `perf/benchmark_population.py` (worker cap **24**, five runs per config, test configs under `test/world_builder/config/`). **`benchmark_v0.4.0.csv`** records **100,000** characters per run (same shape as **`benchmark_v0.3.0.csv`**). Numbers below match the recorded CSV (means and throughput as printed by the benchmark script).

### 100,000 characters per run (v0.3.0 vs v0.4.0)

| Config | v0.3.0 mean (s) | v0.4.0 mean (s) | Wall-time ratio (0.3 / 0.4) | v0.3.0 chars/s | v0.4.0 chars/s |
|--------|-----------------|-----------------|----------------------------|----------------|----------------|
| large  | 0.837           | 0.644           | ~1.30                      | 119,426        | 155,186        |
| medium | 0.780           | 0.595           | ~1.31                      | 128,153        | 167,939        |
| small  | 0.777           | 0.593           | ~1.31                      | 128,675        | 168,649        |

At this scale, 0.4.0 uses roughly **23–24% less wall time** than 0.3.0 on the same workload class (about **1.30×** higher end-to-end throughput for medium and small configs).

## 1. Cache the public Markov loaders (`lru_cache` on filepath)

**Before:** Inner helpers cached by resolved path string, but **`load_preprocessed_markov_model_from_json`** (and **`load_markov_model_from_json`**) still called **`Path(...).resolve()`** on every invocation so repeated first-name draws paid full path resolution and cache lookup setup per call.

**After:** **`@lru_cache(maxsize=32)`** on both public loaders so a hit skips **`resolve()`** and the loader body entirely. JSON read and **`preprocess()`** remain cached per resolved path inside nested **`lru_cache`** helpers.

## 2. Stable default model paths (module-level `Path`)

**Before:** **`generate_male_first_name`** / **`generate_female_first_name`** built **`Path(__file__).parent / "…json"`** on every call. **`functools.lru_cache`** must hash the argument each time; a fresh **`Path`** instance per call forced expensive **`Path.__hash__`** / normalization work on every name.

**After:** **`_DEFAULT_MALE_MODEL`** and **`_DEFAULT_FEMALE_MODEL`** are built once at import (**`Path(__file__).resolve().parent`**). Default generation reuses the same objects, so cache keys are cheap and work is dominated by actual Markov walks.

## 3. Files touched (conceptual map)

| Area | Main locations |
|------|----------------|
| Loader + preprocess cache | `src/namegen/model_builder.py` |
| Default model path constants | `src/namegen/first_name_generator.py` |
| Benchmark artifacts | `perf/benchmark_population.py`, `perf/benchmark_v0.4.0.csv` |

## Reproducing benchmarks

From the repository root (with the package on `PYTHONPATH` or an editable install):

```bash
python perf/benchmark_population.py --runs 5 --workers 24
```

Default **`--count`** is **100000** (matching **`benchmark_v0.4.0.csv`** and the table above). For a quicker smoke run:

```bash
python perf/benchmark_population.py --count 10000 --runs 5 --workers 24
```

Optional flags: **`--count`**, **`--runs`**, **`--workers`** (see the script’s **`--help`**).
