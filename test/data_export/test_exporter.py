"""
Unit tests for the data_export.exporter module.

These tests verify that dict-like objects can be exported to Parquet, JSON, and CSV formats
using the functions provided in the exporter module.
"""

import os
import tempfile
import json

import pandas as pd
import pyarrow.parquet as pq

from data_export import exporter

test_data = {"a": 1, "b": "foo", "c": 3.14}


def test_export_to_parquet():
    """
    Test exporting a dict-like object to a Parquet file and reading it back.
    Ensures the exported data matches the original dict.
    """
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
        exporter.export_to_parquet(test_data, tmp.name)
        tmp.close()
        table = pq.read_table(tmp.name)
        df = table.to_pandas()
        assert df.iloc[0].to_dict() == test_data
    os.remove(tmp.name)


def test_export_to_json():
    """
    Test exporting a dict-like object to a JSON file and reading it back.
    Ensures the exported data matches the original dict.
    """
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        exporter.export_to_json(test_data, tmp.name)
        tmp.close()
        with open(tmp.name) as f:
            data = json.load(f)
        assert data == test_data
    os.remove(tmp.name)


def test_export_to_csv():
    """
    Test exporting a dict-like object to a CSV file and reading it back.
    Ensures the exported data matches the original dict, with correct types.
    """
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        exporter.export_to_csv(test_data, tmp.name)
        tmp.close()
        df = pd.read_csv(tmp.name)
        row = df.iloc[0].to_dict()
        assert row == test_data
    os.remove(tmp.name)
