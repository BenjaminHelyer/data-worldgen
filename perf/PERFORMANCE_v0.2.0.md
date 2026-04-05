# Performance changes in version 0.2.0

This document summarizes the population-generation performance work shipped in **data-worldgen 0.2.0**. Public APIs such as `create_character`, `load_config`, `batch_local`, and `batch_s3` are preserved; the speedups come from internal sampling and batch layout.

## Measured impact (local batch benchmark)

End-to-end timing from `perf/benchmark_population.py` (worker cap 24, five runs per config, test configs under `test/world_builder/config/`). See `benchmark_v0.1.0.csv` and `benchmark_v0.2.0.csv` for raw numbers.

### 10,000 characters per run (vs v0.1.0)

| Config | v0.1.0 mean (s) | v0.2.0 mean (s) | Approx. speedup |
|--------|-----------------|-----------------|-----------------|
| large  | 1.345           | 0.152           | ~8.9x           |
| medium | 1.176           | 0.142           | ~8.3x           |
| small  | 1.236           | 0.138           | ~9.0x           |

Throughput (characters per second, from benchmark summaries) moved from roughly **7.4k–8.5k** to roughly **65k–73k** on the same workload class.

### 100,000 characters per run (baseline for later versions)

At **100,000** characters per run, the same CSV files list v0.2.0 means of **0.906 s** (large), **0.855 s** (medium), and **0.838 s** (small). **v0.3.0** improves on that batch size by roughly **8–10%** wall time; see **`benchmark_v0.3.0.csv`** and **`PERFORMANCE_v0.3.0.md`** for paired 0.2 vs 0.3 numbers. **v0.4.0** improves further on the 100k batch versus 0.3.0 (loader caching and stable default model paths); see **`benchmark_v0.4.0.csv`** and **`PERFORMANCE_v0.4.0.md`**.

## 1. Vectorized categorical (finite) sampling

**Before:** For each character, the pipeline walked finite fields in order, applied factor multipliers in Python dicts, normalized, and drew one category with `random.choices`.

**After:**

- **Precomputation (once per config):** For each categorical field `T`, build a normalized conditional PMF tensor: base weights times per-parent factor tables, normalized over categories of `T`. Parents are every source field `S` in the factor graph such that `T` appears under `S`. If a parent has no `base_probabilities_finite` entry, its category axis is taken from the keys of the factor submap for that parent-target edge (so preset-only parents still work).
- **Implementation:** `src/world_builder/core/finite_pmf.py` (`build_finite_sampling_tables`, `FiniteSamplingTables`).
- **Batch generation:** For `N` characters, gather rows of PMFs via NumPy advanced indexing, then inverse-CDF sampling (`cumsum` plus one uniform per row). Integer indices are decoded to string category names when building rows or `Character` objects.
- **Single character:** `sample_finite_fields` uses the same tables and NumPy sampling (not `random.choices`), so the random stream differs from pre-0.2.0 for that path when a global RNG seed is fixed.

Tables are cached per config object: keyed by `id(config)` with a `weakref` and an **identity check** on lookup so CPython id reuse cannot return another object’s tables.

## 2. Vectorized continuous (distribution) sampling

**Before:** `sample_distribution_fields_with_overrides` looped fields and called `sample_from_config` per character.

**After:**

- **`sample_distribution_fields_batch`** applies overrides (first match wins) and transforms using boolean masks over `N` rows, then draws in bulk for **normal**, **lognormal**, and **truncated_normal** (NumPy / SciPy `truncnorm`).
- **`FunctionBasedDist`** and **`BernoulliBasedDist`** still use the existing per-row `_sample` path where needed.
- **`sample_distribution_fields_with_overrides`** for a single dict delegates to the batch path with `n=1`.

## 3. Batch population entrypoints

**Before:** `batch_local` / `batch_s3` in population mode used `multiprocessing.Pool.map` to run full `create_character` per row (including repeated work and, before fixes, very heavy per-call I/O for names).

**After:**

- **`create_characters_vectorized(config, n, seed=..., name_workers=...)`** in `src/world_builder/population/character.py` runs vectorized finite + distribution sampling in the parent process, then finishes each row (IDs, names, metadata).
- **Batches** pass **`name_workers`** from the same effective worker count as `--workers` / `NUM_WORKERS` (capped by CPU count and entity count). With `name_workers > 1`, character ID, name, and metadata assignment use a **`multiprocessing.Pool`** with per-worker RNG seeding for `random` (used by namegen).

## 4. Name generation: Markov model load caching

**Issue:** `generate_male_first_name` / `generate_female_first_name` called `load_markov_model_from_json` on every invocation, re-reading and re-parsing large JSON models. After moving to a single-process vectorized path, that dominated wall time (~10x slower than v0.1.0 in practice).

**Fix:** `load_markov_model_from_json` in `src/namegen/model_builder.py` resolves the path once and serves models from an **`lru_cache`** keyed by the resolved path string.

Surname generation does not load those JSON files; it was not the main regression.

## 5. New / extended public hooks (core)

From `world_builder.core` (see `src/world_builder/core/__init__.py`):

- `build_finite_sampling_tables` – build PMF tables without going through the sampler cache.
- `get_finite_sampling_tables` – return cached tables (build on first use).
- `sample_finite_fields_batch`, `sample_distribution_fields_batch`.
- `FiniteSamplingTables`, `distribution_sample_to_python`.

`world_builder.population` also exports **`create_characters_vectorized`** for callers who want the fast path outside the batch scripts.

## 6. Files touched (conceptual map)

| Area | Main locations |
|------|----------------|
| PMF precompute | `src/world_builder/core/finite_pmf.py` |
| Sampling + cache + batch APIs | `src/world_builder/core/sampling.py` |
| Vectorized character batch | `src/world_builder/population/character.py` |
| Markov JSON cache | `src/namegen/model_builder.py` |
| Local / S3 batch | `src/world_builder/batch_local.py`, `src/world_builder/batch_s3.py` |
| Benchmark artifacts | `perf/benchmark_population.py`, `perf/benchmark_v0.2.0.csv`, `perf/benchmark_v0.3.0.csv`, `perf/benchmark_v0.4.0.csv` |

Ecosystem (`create_animal`) still uses the shared finite/distribution sampling improvements where applicable; batch animal generation remains pool-based per entity.

## Reproducing benchmarks

From the repository root (with the package on `PYTHONPATH` or an editable install):

```bash
python perf/benchmark_population.py
```

Optional flags: `--count`, `--runs`, `--workers` (see the script’s `--help`).
