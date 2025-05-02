"""
Module to build the models for name generation.
"""

from collections import defaultdict, Counter
import random

import pandas as pd

def build_weighted_markov_chain(df: pd.DataFrame, n: int = 3) -> dict:
    """
    Builds a weighted Markov chain of order n-1 using name frequencies.
    
    Args:
        df: DataFrame with columns 'Name' and 'Count'
        n: Order of the n-gram (e.g., 3 = trigram)
    
    Returns:
        dict mapping (n-1)-grams to distributions over next characters
    """
    transitions = defaultdict(Counter)

    # iterate through each row of the df, getting frequencies for each transition
    for _, row in df.iterrows():
        name = row["Name"].lower()
        count = row["Count"]
        padded = "~" * (n - 1) + name + "$"

        for i in range(len(padded) - n + 1):
            prefix = padded[i:i+n-1]
            next_char = padded[i+n-1]
            transitions[prefix][next_char] += count  # weight by count

    # normalization step
    model = {}
    for prefix, counter in transitions.items():
        total = sum(counter.values())
        model[prefix] = {char: freq / total for char, freq in counter.items()}

    return model


def generate_name(markov_model: dict, n: int = 3, max_len: int = 12) -> str:
    """
    Samples a name from the weighted Markov model.
    """
    prefix = "~" * (n - 1)
    name = ""

    while True:
        probs = markov_model.get(prefix)
        if not probs:
            break  # fallback if we hit a dead-end
        chars, weights = zip(*probs.items())
        next_char = random.choices(chars, weights=weights)[0]
        if next_char == "$" or len(name) >= max_len:
            break
        name += next_char
        prefix = prefix[1:] + next_char

    return name.capitalize()
