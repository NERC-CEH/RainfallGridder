#!/usr/bin/env python

"""Pytest config file. Contains test fixtures of rainfall data."""

import datetime

import numpy as np
import polars as pl
import pytest

from rainfall_gridder.prepare_data import metadata_preparer

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
    return metadata_preparer.add_completeness_to_metadata(data, metadata,
                                                                    station_id_col='station_id',
                                                                    date_time_col='date_time')
