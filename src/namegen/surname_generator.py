"""
Generates a surname.

Based on a random prefix of a planet and a random suffix.
"""

import random

from .planets_list import PLANETS_LIST
from .surname_suffix_list import HUMAN_SUFFIXES, TWILEK_SUFFIXES, TRANDOSHAN_SUFFIXES

suffix_lookup = {
    "human": HUMAN_SUFFIXES,
    "twilek": TWILEK_SUFFIXES,
    "trandoshan": TRANDOSHAN_SUFFIXES,
}


def extract_planet_root(name: str) -> str:
    """
    Extracts the first word of a planet name and converts it to lowercase.

    Args:
        name: The full planet name (e.g. "New Alderaan")

    Returns:
        The lowercase first word of the planet name (e.g. "new")
    """
    return name.split()[0].lower()


def random_segment(word: str, min_len: int = 2, max_len: int = 5) -> str:
    """
    Extracts a random segment of a word between min_len and max_len characters.

    Args:
        word: The input word to extract a segment from
        min_len: Minimum length of the segment (default: 2)
        max_len: Maximum length of the segment (default: 5)

    Returns:
        A random segment of the input word. If the word is shorter than min_len,
        returns the entire word.
    """
    if len(word) <= min_len:
        return word
    start = random.randint(0, len(word) - min_len)
    end = min(len(word), start + random.randint(min_len, max_len))
    return word[start:end]


def generate_surname(species=None):
    """
    Generates a surname.

    Currently generates based on a list of planets, using that as the prefix.
    Then it takes the suffix based on a list of known species suffixes.
    """
    suffixes = []
    if not species or species not in suffix_lookup:
        suffixes = HUMAN_SUFFIXES
    else:
        suffixes = suffix_lookup[species]

    root_word = extract_planet_root(random.choice(PLANETS_LIST))
    segment = random_segment(root_word)
    suffix = random.choice(suffixes)

    return (segment + suffix).capitalize()
