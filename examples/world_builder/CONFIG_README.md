# Population config authoring guide

This document describes how to write JSON files that load as `PopulationConfig` and drive `world_builder.population` sampling (`load_config`, `create_characters_vectorized`, batch scripts). The **baseline pipeline** is:

1. Sample every **finite** (categorical) field in dependency order using conditional PMFs built from `base_probabilities_finite` and `factors`.
2. Sample every **distribution** field from `base_probabilities_distributions`, applying optional **overrides** then **transforms** using already-sampled finite fields.
3. Attach **metadata** constants, then assign IDs and names in code.

You can extend supported distributions or transformations in Python, but the **roles** of those sections (finite vs continuous, factor graph vs distribution transforms) should stay as described here.

---

## Top-level shape

Only these keys are defined on `PopulationConfig`. Other keys at the root of the JSON are **ignored** by Pydantic (they are not loaded), so do not rely on undocumented sections being applied.

| Key | Required | Role |
|-----|----------|------|
| `base_probabilities_finite` | Yes | Categorical fields and their PMFs (each category block sums to 1.0). |
| `base_probabilities_distributions` | Yes | Continuous (or special) fields keyed by distribution objects. |
| `factors` | No | Non-negative multipliers on categorical conditional probabilities. |
| `override_distributions` | No | Replace a distribution for rows matching a condition (first match wins). |
| `transform_distributions` | No | Shift or scale parameters of a distribution from the base after overrides. |
| `metadata` | No | String constants copied onto every entity (e.g. planet name). |

---

## `base_probabilities_finite`

- For each **field name** (e.g. `species`, `city`), provide a map of **value string** to **probability** (float).
- Probabilities for each field must **sum to 1.0** (within floating-point tolerance).
- Field names are arbitrary strings, but they must be consistent everywhere they are referenced (factors, overrides, transforms).

These fields are sampled first. Sampling order is: keys listed in `factors` that are finite fields (in insertion order), then any remaining finite fields not listed in `factors`.

---

## `base_probabilities_distributions`

- Each key is a **field name** (e.g. `age`, `height`). Each value is a **distribution object** with a `"type"` field.
- Supported types that participate in the fast vectorized path (normal / lognormal / truncated normal) are listed in `world_builder.distributions_config` and `DISTRIBUTION_REGISTRY`: `normal`, `lognormal`, `truncated_normal`.
- Additional types such as `function_based` and Bernoulli-based distributions exist for specialized sampling; they may depend on **numerical** fields sampled earlier in the same `base_probabilities_distributions` mapping. **Order matters**: put dependent distribution fields **after** the fields they read in the JSON object (Python preserves insertion order).

Example (truncated normal):

```json
"age": {
  "type": "truncated_normal",
  "mean": 30,
  "std": 20,
  "lower": 0
}
```

`upper` is optional on truncated normal (defaults to infinity in the model).

---

## `factors`

Purpose: adjust **categorical** probabilities. Structure:

```text
factor_field -> influenced_field -> factor_value -> { influenced_value: multiplier }
```

- **`factor_field`** must be a key in `base_probabilities_finite` (the outer keys of `factors` are also required to appear in the union of finite and distribution field names for validation).
- **`influenced_field`** must be a key in `base_probabilities_finite`. The inner map’s values are multipliers on categories of that field; every **subkey** must be a category listed in `base_probabilities_finite[influenced_field]`.

**Critical:** `factors` cannot condition **continuous** fields (for example `height` or `weight`). Use `transform_distributions` or `override_distributions` for those.

- Every **key** in `key_map` must be a category of `factor_field`.
- Every **subkey** must be a category of `influenced_field`.
- All multipliers must be **non-negative** numbers.
- The graph must be **acyclic** (DAG). The **insertion order** of keys in `factors` defines a topological constraint: if `A` influences `B`, then `B` must appear **later** in the `factors` object than `A` when both are keys in `factors`.

---

## `override_distributions`

A JSON **array** of objects. Each object has:

- `field`: name of a key in `base_probabilities_distributions`.
- `condition`: object mapping **finite** field names to a single string value that must exist in that field’s PMF.
- `distribution`: a full distribution object (same shape as in `base_probabilities_distributions`).

**First matching override wins** per row (later overrides do not apply to rows already matched). Matching is applied before `transform_distributions`.

---

## `transform_distributions`

Shape:

```text
distribution_field -> trait_field -> trait_value -> { "mean_shift": <float>, "std_mult": <float> }
```

- `distribution_field` must be a key in `base_probabilities_distributions`.
- `trait_field` must be a **finite** field whose values are already sampled (e.g. `species`, `city`).
- Each transform object is a `DistributionTransformOperation`: optional **`mean_shift`** (added to the mean) and **`std_mult`** (positive multiplier on the standard deviation). Omitted keys behave as 0 and 1 respectively.

**Semantics:** For each row, the base distribution is initialized from the (possibly overridden) parameters. Then, for each `(trait_field, trait_value)` entry that matches the row, the code applies `mean += mean_shift` and `std *= std_mult`. Transforms are **not** full multiplicative composition of traits on top of each other in the sense of “multiply final mean by species then by gender”; they are additive shifts and std scaling from the **same base** parameters, applied in **iteration order** of the nested `transform_distributions` structure. To approximate multiplicative effects on the mean, use `mean_shift = base_mean * (factor - 1)` from a reference baseline.

Use JSON keys **`mean_shift`** and **`std_mult`** (underscores), as expected by the Pydantic model.

---

## `metadata`

- A flat object of **string** keys to **string** values.
- Values are copied onto each sampled character (e.g. `"planet": "Tatooine"`).

---

## Validation checklist

Before relying on a config:

1. Every finite PMF sums to 1.0.
2. Every `factors` key and subkey references categories that exist in the corresponding `base_probabilities_finite` blocks.
3. `factors` has no cycles and respects key order (influencer before influenced when both are factor keys).
4. Overrides reference only finite `condition` keys and valid category values.
5. Transforms reference distribution fields and finite trait fields only.

Load with:

```python
from pathlib import Path
from world_builder.population.config import load_config

config = load_config(Path("your_config.json"))
```

---

## Reference files

Examples in this directory:

- `wb_config.json` — baseline population config.
- `wb_extended_config.json` — adds height and weight distributions and species-based `transform_distributions`.

Implementation details live in `src/world_builder/population/config.py`, `src/world_builder/core/sampling.py`, and `src/world_builder/core/finite_pmf.py`.

---

## Extending distributions or transforms

New distribution types or sampling behavior should plug into `world_builder.distributions_config` and `core.sampling.sample_distribution_fields_batch` (and the non-batch path) while keeping:

- Finite vs distribution separation.
- Factor graph rules for **categorical** conditioning only.
- `transform_distributions` as parameter shifts on distribution fields after overrides.

That keeps the mental model above stable for config authors.
