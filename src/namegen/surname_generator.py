"""
Generates a surname.

Based on a random prefix of a planet and a random suffix.
"""

import random

from .planets_list import PLANETS_LIST


def extract_planet_root(name):
    return name.split()[0].lower()


def random_segment(word, min_len=2, max_len=5):
    if len(word) <= min_len:
        return word
    start = random.randint(0, len(word) - min_len)
    end = min(len(word), start + random.randint(min_len, max_len))
    return word[start:end]


def generate_surname(suffixes=None):
    """
    Generates a surname.

    Currently generates based on a list of planets, using that as the prefix.
    Then it takes the suffix based on a list of known species suffixes.
    """
    if suffixes is None:
        human_suffixes = [
            "son",
            "er",
            "ar",
            "an",
            "en",
            "ell",
            "in",
            "ix",
            "or",
            "ius",
            "man",
            "ley",
            "win",
            "eth",
            "dan",
            "vek",
        ]
        twilek_suffixes = [
            "eth",
            "ira",
            "urra",
            "ven",
            "asha",
            "il",
            "ren",
            "ae",
            "nek",
            "eesh",
            "ali",
            "ohl",
            "ami",
        ]
        trandoshan_suffixes = [
            "ssk",
            "arsh",
            "okk",
            "rak",
            "nak",
            "zor",
            "gash",
            "azz",
            "och",
            "thok",
            "kren",
            "usk",
            "drass",
        ]
        suffixes = human_suffixes + twilek_suffixes + trandoshan_suffixes

    root_word = extract_planet_root(random.choice(PLANETS_LIST))
    segment = random_segment(root_word)
    suffix = random.choice(suffixes)

    return (segment + suffix).capitalize()
