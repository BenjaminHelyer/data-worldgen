"""
Module to build the models for name generation.

To utilize this code with your own names, please run build_weighted_markov_chain
on a Pandas dataframe that contains the columns 'Name' and 'Count'.

These models are simply JSON under the hood, nothing too fancy.
"""

from collections import defaultdict, Counter
from functools import lru_cache
import bisect
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple, Union

import pandas as pd

PreprocessedTable = Dict[str, Tuple[List[str], List[float]]]


def build_weighted_markov_chain(
    df: pd.DataFrame, n: int = 3, start_padding: str = "~", end_padding: str = "$"
) -> dict:
    """
    Builds a weighted Markov chain of order n-1 using name frequencies.

    Args:
        df: DataFrame with columns 'Name' and 'Count'
        n: Order of the n-gram (e.g., 3 = trigram)
        start_padding: Character used to pad the start of the name
        end_padding: Character used to mark the end of a name

    Returns:
        dict mapping (n-1)-grams to distributions over next characters
    """
    transitions = defaultdict(Counter)

    for _, row in df.iterrows():
        name = row["Name"].lower()
        count = row["Count"]
        padded = start_padding * (n - 1) + name + end_padding

        for i in range(len(padded) - n + 1):
            prefix = padded[i : i + n - 1]
            next_char = padded[i + n - 1]
            transitions[prefix][next_char] += count

    model = {}
    for prefix, counter in transitions.items():
        total = sum(counter.values())
        model[prefix] = {char: freq / total for char, freq in counter.items()}

    return model


def preprocess(raw: Dict[str, Dict[str, float]]) -> PreprocessedTable:
    """
    Build a lookup table with sorted character lists and cumulative probabilities.

    Each state's transition map is converted to (chars, cumprobs) where chars is
    sorted and cumprobs[i] is the sum of probabilities for chars[0] through
    chars[i]. The input dict is not modified.

    Args:
        raw: State keys mapping to next-character probability dicts.

    Returns:
        Mapping from state to (sorted next characters, cumulative probabilities).

    Raises:
        ValueError: If any state's probabilities sum outside [0.999, 1.001].
    """
    out: PreprocessedTable = {}
    for state, trans in raw.items():
        items = sorted(trans.items(), key=lambda kv: kv[0])
        chars = [c for c, _ in items]
        probs = [float(p) for _, p in items]
        total = sum(probs)
        if not (0.999 <= total <= 1.001):
            raise ValueError(
                f"probabilities for state {state!r} sum to {total}, expected ~1.0"
            )
        cumprobs: List[float] = []
        acc = 0.0
        for p in probs:
            acc += p
            cumprobs.append(acc)
        out[state] = (chars, cumprobs)
    return out


def sample(table: PreprocessedTable, state: str) -> str:
    """
    Draw one next character for the given state using inverse CDF sampling.

    Args:
        table: Preprocessed table from preprocess().
        state: Current n-gram state key.

    Returns:
        The sampled next character (single-character string).

    Raises:
        KeyError: If state is not present in table.
    """
    chars, cumprobs = table[state]
    u = random.random()
    idx = bisect.bisect_left(cumprobs, u)
    if idx >= len(chars):
        idx = len(chars) - 1
    return chars[idx]


def generate_name(
    table: PreprocessedTable,
    start: str = "~~",
    stop: str = "$",
    max_len: int = 12,
) -> str:
    """
    Walk the bigram (or fixed-width) chain until the stop token is sampled.

    The stop character is never appended to the returned string. The result is
    capitalized for display (same convention as training, which uses lowercase).

    Args:
        table: Preprocessed transition table.
        start: Initial state (length matches model prefix width, e.g. \"~~\").
        stop: Terminal next-character symbol (default \"$\" matches shipped JSON).
        max_len: Maximum number of characters before stopping.

    Returns:
        Generated name string.
    """
    state = start
    name_chars: List[str] = []
    while True:
        if state not in table:
            break
        ch = sample(table, state)
        if ch == stop or len(name_chars) >= max_len:
            break
        name_chars.append(ch)
        state = state[1:] + ch
    return "".join(name_chars).capitalize()


def generate_batch(
    table: PreprocessedTable,
    n: int,
    start: str = "~~",
    stop: str = "$",
    max_len: int = 12,
) -> list[str]:
    """
    Generate n names in parallel, advancing all active chains each step.

    Finished chains (stop sampled, max length, or missing state) are removed
    from the active set. Returned list index i corresponds to the i-th chain.

    Args:
        table: Preprocessed transition table.
        n: Number of names to generate.
        start: Initial state for every chain.
        stop: Terminal next-character symbol.
        max_len: Maximum characters per name before stopping.

    Returns:
        List of n generated names, capitalized.
    """
    if n <= 0:
        return []
    states = [start] * n
    names: List[List[str]] = [[] for _ in range(n)]
    active = set(range(n))

    while active:
        finished: List[int] = []
        for i in active:
            st = states[i]
            if st not in table:
                finished.append(i)
                continue
            ch = sample(table, st)
            if ch == stop or len(names[i]) >= max_len:
                finished.append(i)
                continue
            names[i].append(ch)
            states[i] = st[1:] + ch
        for i in finished:
            active.discard(i)

    return ["".join(parts).capitalize() for parts in names]


def save_markov_model_to_json(
    model: Dict[str, Dict[str, float]], filepath: str
) -> None:
    """
    Saves a Markov model to a JSON file.

    Args:
        model: The Markov model as a dict of dicts (prefix → next_char → probability)
        filepath: Path to the output JSON file
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2)


@lru_cache(maxsize=32)
def _load_markov_model_from_json_cached(resolved_path: str) -> Dict[str, Dict[str, float]]:
    with open(resolved_path, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=32)
def _load_preprocessed_markov_model_from_json_cached(
    resolved_path: str,
) -> PreprocessedTable:
    raw = _load_markov_model_from_json_cached(resolved_path)
    return preprocess(raw)


@lru_cache(maxsize=32)
def load_markov_model_from_json(filepath: Union[str, Path]) -> Dict[str, Dict[str, float]]:
    """
    Loads a Markov model from a JSON file.

    Models are cached by filepath argument (and by resolved path inside nested
    caches) so repeated name generation does not re-resolve, re-read, or
    re-parse the same file.

    Args:
        filepath: Path to the JSON file containing the model

    Returns:
        The Markov model as a dict of dicts (prefix → next_char → probability)
    """
    resolved = str(Path(filepath).resolve())
    return _load_markov_model_from_json_cached(resolved)


@lru_cache(maxsize=32)
def load_preprocessed_markov_model_from_json(
    filepath: Union[str, Path],
) -> PreprocessedTable:
    """
    Load a Markov model from JSON and preprocess it for fast sampling.

    Both raw JSON load and preprocess are cached by resolved path.

    Args:
        filepath: Path to the JSON model file.

    Returns:
        Preprocessed table suitable for sample(), generate_name(), generate_batch().
    """
    resolved = str(Path(filepath).resolve())
    return _load_preprocessed_markov_model_from_json_cached(resolved)
