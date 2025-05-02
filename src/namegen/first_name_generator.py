"""
first_name_generator.py

This module provides convenience functions to generate male or female first names
using pretrained Markov chain models saved as JSON files.

By default, the module will look for the following files in the same directory:
    - 'first_name_markov_model_M.json'
    - 'first_name_markov_model_F.json'

Usage:
    from first_name_generator import generate_male_first_name, generate_female_first_name

    print(generate_male_first_name())
    print(generate_female_first_name())

You may also provide a custom file path for the model:
    generate_male_first_name(filepath=Path("/my/custom/model.json"))
"""

from pathlib import Path
from namegen import load_markov_model_from_json, generate_name


def generate_male_first_name(
    filepath: Path = None, n: int = 3, max_len: int = 12
) -> str:
    """
    Generates a male first name using a pretrained Markov model.

    Args:
        filepath: Optional Path to a custom JSON model file.
        n: The n-gram order used in the model (default: 3)
        max_len: Maximum name length (default: 12)

    Returns:
        A male first name string.
    """
    if filepath is None:
        filepath = Path(__file__).parent / "first_name_markov_model_M.json"
    model = load_markov_model_from_json(filepath)
    return generate_name(model, n=n, max_len=max_len)


def generate_female_first_name(
    filepath: Path = None, n: int = 3, max_len: int = 12
) -> str:
    """
    Generates a female first name using a pretrained Markov model.

    Args:
        filepath: Optional Path to a custom JSON model file.
        n: The n-gram order used in the model (default: 3)
        max_len: Maximum name length (default: 12)

    Returns:
        A female first name string.
    """
    if filepath is None:
        filepath = Path(__file__).parent / "first_name_markov_model_F.json"
    model = load_markov_model_from_json(filepath)
    return generate_name(model, n=n, max_len=max_len)
