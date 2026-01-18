import pytest
import pandas as pd

from unittest.mock import patch

from world_builder.population import dashboard as population_dashboard


@pytest.fixture
def example_dataframe(tmp_path):
    """Create a real Parquet file for testing load_data()."""
    df = pd.DataFrame(
        {
            "first_name": ["Ahsoka", "Padmé", "Obi-Wan"],
            "surname": ["Tano", "Naberrie", "Kenobi"],
            "species": ["Togruta", "Human", "Human"],
            "gender": ["female", "female", "male"],
            "age": [17, 27, 35],
            "allegiance": ["Rebel", "Republic", "Jedi"],
            "character_id": ["abc", "def", "ghi"],
        }
    )
    parquet_path = tmp_path / "population.parquet"
    df.to_parquet(parquet_path)
    return parquet_path


def test_main_smoke_with_real_dataframe(monkeypatch, example_dataframe):
    """
    A true smoke test: use real data, run the main dashboard logic,
    and confirm it executes end-to-end with no exceptions.
    """
    # Override the file path used by load_data()
    monkeypatch.setattr(
        population_dashboard, "load_data", lambda: pd.read_parquet(example_dataframe)
    )

    # Run the Streamlit logic end-to-end (not as a server, just functionally)
    population_dashboard.run_dashboard_main()
