#!/usr/bin/env python

"""Pytest config file. Contains test fixtures of rainfall data."""

import datetime

import polars as pl
import pytest

from rainfall_gridder.prepare_data import metadata_preparer


STATION_DATA = [
    {
        "station_id": "240662TP",
        "station_name": "Lilley Manor",
        "easting": 511070,
        "northing": 227720,
        "operator": "EA",
        "start_date": datetime.datetime(2024, 11, 1, 0, 0, 0),
        "end_date": datetime.datetime(2024, 12, 31, 23, 45, 0),
        "completeness": 100.0,
    },
    {
        "station_id": "246424TP",
        "station_name": "Holland Park",
        "easting": 524658,
        "northing": 179586,
        "operator": "EA",
        "start_date": datetime.datetime(2024, 11, 1, 0, 0, 0),
        "end_date": datetime.datetime(2024, 12, 31, 23, 45, 0),
        "completeness": 100.0,
    },
    {
        "station_id": "240816TP",
        "station_name": "Whitwell",
        "easting": 519197,
        "northing": 220812,
        "operator": "EA",
        "start_date": datetime.datetime(2024, 11, 1, 0, 0, 0),
        "end_date": datetime.datetime(2024, 12, 31, 23, 45, 0),
        "completeness": 100.0,
    },
]

STATION_SCHEMA = {
    "station_id": pl.Utf8,
    "station_name": pl.Utf8,
    "easting": pl.Int64,
    "northing": pl.Int64,
    "operator": pl.Utf8,
    "start_date": pl.Datetime("us"),
    "end_date": pl.Datetime("us"),
    "completeness": pl.Float64,
}


@pytest.fixture
def chess_rainfall_data() -> pl.DataFrame:
    return pl.read_parquet("test_data/chess_rainfall_data.parquet")


@pytest.fixture
def chess_rainfall_metadata() -> pl.DataFrame:
    return pl.read_parquet("test_data/chess_rainfall_metadata.parquet")


@pytest.fixture
def chess_rainfall_metadata_w_completeness() -> pl.DataFrame:
    data = pl.read_parquet("test_data/chess_rainfall_data.parquet")
    metadata = pl.read_parquet("test_data/chess_rainfall_metadata.parquet")
    return metadata_preparer.add_completeness_to_metadata(
        data, metadata, station_id_col="station_id", date_time_col="date_time"
    )


@pytest.fixture
def example_metadata() -> pl.DataFrame:
    """Fixture returning a DataFrame with sample station data."""
    return pl.DataFrame(STATION_DATA, schema=STATION_SCHEMA)


@pytest.fixture
def incomplete_example_metadata() -> pl.DataFrame:
    """Fixture with varied completeness values for testing filtering/thresholds."""
    data = [
        {**STATION_DATA[0], "completeness": 45.5},
        {**STATION_DATA[1], "completeness": 78.2},
        {**STATION_DATA[2], "completeness": 100.0},
    ]
    return pl.DataFrame(data, schema=STATION_SCHEMA)


@pytest.fixture
def example_metadata_with_nulls_df() -> pl.DataFrame:
    """Fixture with null values to test null handling."""
    data = [
        {**STATION_DATA[0], "end_date": None, "completeness": None},
        {**STATION_DATA[1]},
        {**STATION_DATA[2], "operator": None},
    ]
    return pl.DataFrame(data, schema=STATION_SCHEMA)


@pytest.fixture
def multi_operator_example_metadata() -> pl.DataFrame:
    """Fixture with multiple operators for testing groupby/operator filtering."""
    data = [
        {**STATION_DATA[0], "operator": "EA"},
        {**STATION_DATA[1], "operator": "SEPA"},
        {**STATION_DATA[2], "operator": "NRW"},
    ]
    return pl.DataFrame(data, schema=STATION_SCHEMA)


def make_station_df(**overrides) -> pl.DataFrame:
    """
    Factory function to build a single-row station DataFrame with custom field values.

    Usage:
        df = make_station_df(station_id="999TP", completeness=55.0)
    """
    row = {**STATION_DATA[0], **overrides}
    return pl.DataFrame([row], schema=STATION_SCHEMA)
