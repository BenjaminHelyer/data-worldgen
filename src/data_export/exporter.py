"""
Provides functions for exporting dict-like objects to various file formats.

This module contains utility functions to export dictionary data to common data formats
including Parquet, JSON, and CSV. Each export function takes a dictionary and filepath
as input and handles the conversion and file writing process.

Supported formats:
- Parquet: Columnar storage format, good for large datasets
- JSON: Human-readable text format
- CSV: Simple tabular format
"""

import pandas as pd
from typing import Any, Dict


def export_to_parquet(data: Dict[str, Any], filepath: str) -> None:
    """
    Export a dict-like object to a Parquet file.
    Args:
        data: The dict-like object to export.
        filepath: The path to the output Parquet file.
    """
    df = pd.DataFrame([data])
    df.to_parquet(filepath)


def export_to_json(data: Dict[str, Any], filepath: str) -> None:
    """
    Export a dict-like object to a JSON file.
    Args:
        data: The dict-like object to export.
        filepath: The path to the output JSON file.
    """
    import json

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def export_to_csv(data: Dict[str, Any], filepath: str) -> None:
    """
    Export a dict-like object to a CSV file.
    Args:
        data: The dict-like object to export.
        filepath: The path to the output CSV file.
    """
    df = pd.DataFrame([data])
    df.to_csv(filepath, index=False)
