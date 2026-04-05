# Performance changes in version 0.3.0

This document summarizes the **namegen Markov chain** work shipped in **data-worldgen 0.3.0**. Population batch entrypoints (`batch_local`, `batch_s3`, `create_characters_vectorized`) and the vectorized finite or distribution sampling from 0.2.0 are unchanged; 0.3.0 removes per-draw overhead inside Markov name sampling.

## Measured impact (local batch benchmark)

End-to-end timing from `perf/benchmark_population.py` (worker cap 24, five runs per config, test configs under `test/world_builder/config/`). **`benchmark_v0.3.0.csv`** records **100,000** characters per run (same shape as the 100k rows in **`benchmark_v0.2.0.csv`**). Use **`--count 10000`** if you want a smaller batch size for local iteration; those runs are not stored in `benchmark_v0.3.0.csv`.

### 100,000 characters per run (v0.2.0 vs v0.3.0)

| Config | v0.2.0 mean (s) | v0.3.0 mean (s) | Wall-time ratio (0.2 / 0.3) | v0.2.0 chars/s | v0.3.0 chars/s |
|--------|-----------------|-----------------|----------------------------|----------------|----------------|
| large  | 0.906           | 0.837           | ~1.08                      | 110,345        | 119,426        |
| medium | 0.855           | 0.780           | ~1.10                      | 116,945        | 128,153        |
| small  | 0.838           | 0.777           | ~1.08                      | 119,328        | 128,675        |

At this scale, 0.3.0 is roughly **8–10% faster** end-to-end on the same workload class, in addition to the Markov sampling change (precomputed cumulative weights and `bisect` instead of per-draw `random.choices` work).

## 1. Preprocess transitions at load time

**Before:** Each next character used `random.choices` on the raw dict weights, which rebuilds normalized cumulative weights internally on every call.

**After:**

- **`preprocess(raw)`** in `src/namegen/model_builder.py` converts each state’s transition map into **`(chars, cumprobs)`**: `chars` sorted, `cumprobs` the running sum of probabilities. The input dict is not mutated. If any state’s probabilities sum outside **[0.999, 1.001]**, preprocessing raises **`ValueError`**.
- **`load_preprocessed_markov_model_from_json`** resolves the path once and caches the **preprocessed** table per resolved path (in addition to the existing raw JSON `lru_cache`).

## 2. Sampling: `random.random` + `bisect`

**`sample(table, state)`** draws with **`random.random()`** and **`bisect.bisect_left`** on the precomputed cumulative array. **`random.choices` is not used** anywhere in the namegen sampling path.

## 3. Batch name generation (optional API)

**`generate_batch(table, n, ...)`** advances **n** chains in parallel each step, removing finished chains when the stop token is sampled, max length is reached, or the state is missing from the table. This is available for callers that want many names without a Python loop over **`generate_name`**.

## 4. Public exports

From `namegen` (see `src/namegen/__init__.py`): **`preprocess`**, **`sample`**, **`generate_name`**, **`generate_batch`**, **`load_preprocessed_markov_model_from_json`**, alongside the existing build or save or load helpers.

**`generate_male_first_name` / `generate_female_first_name`** use the preprocessed loader and the new **`generate_name`** signature (`start` from `n`, **`stop="$"`** for shipped JSON models).

## 5. Files touched (conceptual map)

| Area | Main locations |
|------|----------------|
| Markov preprocess + sampling + batch | `src/namegen/model_builder.py` |
| First-name convenience API | `src/namegen/first_name_generator.py` |
| Package exports | `src/namegen/__init__.py` |
| Regression tests | `test/namegen/test_markov_sampling.py`, `test/namegen/test_model_builder.py` |
| Benchmark artifacts | `perf/benchmark_population.py`, `perf/benchmark_v0.3.0.csv` |

## Reproducing benchmarks

From the repository root (with the package on `PYTHONPATH` or an editable install):

```bash
python perf/benchmark_population.py --runs 5 --workers 24
```

Default **`--count`** is **100000** (matching `benchmark_v0.3.0.csv` and the table above). For a quicker smoke run:

```bash
python perf/benchmark_population.py --count 10000 --runs 5 --workers 24
```

Optional flags: `--count`, `--runs`, `--workers` (see the script’s `--help`).
