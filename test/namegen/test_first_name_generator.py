import pytest
from pathlib import Path

from namegen import generate_male_first_name, generate_female_first_name


@pytest.mark.parametrize(
    "generate_func", [generate_male_first_name, generate_female_first_name]
)
def test_generate_first_name_defaults(generate_func):
    """
    Smoke test for default male and female name generation.

    Ensures:
    - Each function returns a non-empty string
    - Multiple generations are allowed
    - Default JSON models exist and are readable
    """
    names = [generate_func() for _ in range(5)]

    for name in names:
        assert isinstance(name, str)
        assert len(name) > 0
        assert name[0].isupper()
