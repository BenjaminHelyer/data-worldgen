"""
Tests for preprocessed Markov sampling (cumulative arrays + bisect).
"""

from __future__ import annotations

import random
from collections import Counter

import pytest

from namegen.model_builder import (
    generate_batch,
    generate_name,
    preprocess,
    sample,
)


def test_preprocess_structure():
    raw = {
        "~~": {"z": 0.1, "a": 0.2, "m": 0.7},
        "ab": {"c": 0.5, "d": 0.5},
    }
    before = {k: dict(v) for k, v in raw.items()}
    table = preprocess(raw)
    assert raw == before

    for state, tup in table.items():
        assert isinstance(tup, tuple) and len(tup) == 2
        chars, cumprobs = tup
        assert isinstance(chars, list)
        assert isinstance(cumprobs, list)
        assert len(chars) == len(cumprobs)
        assert chars == sorted(chars)
        assert cumprobs[-1] == pytest.approx(1.0, abs=1e-9)


def test_sample_distribution():
    raw = {"aa": {"x": 0.25, "y": 0.75}}
    table = preprocess(raw)
    random.seed(12345)
    counts: Counter[str] = Counter()
    n = 400_000
    for _ in range(n):
        counts[sample(table, "aa")] += 1
    assert counts["x"] / n == pytest.approx(0.25, rel=0.01)
    assert counts["y"] / n == pytest.approx(0.75, rel=0.01)


def test_generate_name_no_stop_token():
    raw = {
        "~~": {"a": 0.25, "b": 0.25, "~": 0.5},
        "~a": {"~": 1.0},
        "~b": {"~": 1.0},
    }
    table = preprocess(raw)
    random.seed(0)
    for _ in range(500):
        name = generate_name(table, start="~~", stop="~")
        assert "~" not in name


def test_generate_name_only_valid_chars():
    raw = {
        "~~": {"a": 0.4, "b": 0.4, "$": 0.2},
        "~a": {"$": 1.0},
        "~b": {"$": 1.0},
    }
    table = preprocess(raw)
    valid = set()
    for trans in raw.values():
        valid.update(trans.keys())
    random.seed(1)
    for _ in range(200):
        name = generate_name(table, start="~~", stop="$")
        for ch in name:
            assert ch.lower() in valid


def test_generate_batch_count():
    raw = {"~~": {"$": 1.0}}
    table = preprocess(raw)
    names = generate_batch(table, 500, start="~~", stop="$")
    assert len(names) == 500


def test_invalid_probabilities():
    raw = {"s": {"a": 1.5}}
    with pytest.raises(ValueError):
        preprocess(raw)
