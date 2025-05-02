"""
Module to build the models for name generation.

To utilize this code with your own names, please run build_weighted_markov_chain
on a Pandas dataframe that contains the columns 'Name' and 'Count'.

These models are simply JSON under the hood, nothing too fancy.
"""

from collections import defaultdict, Counter
import random
import json
from typing import Dict

import pandas as pd


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


def generate_name(
    markov_model: dict,
    n: int = 3,
    max_len: int = 12,
    start_padding: str = "~",
    end_padding: str = "$",
) -> str:
    """
    Samples a name from the weighted Markov model.

    Args:
        markov_model: The prefix-to-next-char distribution
        n: Order of the n-gram model
        max_len: Maximum length of generated name
        start_padding: Character used to pad the beginning
        end_padding: Character used to signal name ending

    Returns:
        A generated name string
    """
    prefix = start_padding * (n - 1)
    name = ""

    while True:
        probs = markov_model.get(prefix)
        if not probs:
            break
        chars, weights = zip(*probs.items())
        next_char = random.choices(chars, weights=weights)[0]
        if next_char == end_padding or len(name) >= max_len:
            break
        name += next_char
        prefix = prefix[1:] + next_char

    return name.capitalize()


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


def load_markov_model_from_json(filepath: str) -> Dict[str, Dict[str, float]]:
    """
    Loads a Markov model from a JSON file.

    Args:
        filepath: Path to the JSON file containing the model

    Returns:
        The Markov model as a dict of dicts (prefix → next_char → probability)
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
