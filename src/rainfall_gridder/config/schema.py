from pathlib import Path

import polars as pl
import xarray as xr
from pydantic import BaseModel, Field


class ColumnConfig(BaseModel):
    station_id_col: str = "station_id"
    station_name_col: str = "station_name"
    date_time_col: str = "date_time"
    start_date_col: str = "start_date"
    end_date_col: str = "end_date"
    easting_col: str = "easting"
    northing_col: str = "northing"
    precipitation_col: str = "precipitation"


class RainGaugeMetadataConfig(BaseModel):
    path: Path


class RainGaugeDataConfig(BaseModel):
    path: Path


class GriddedRainfallConfig(BaseModel):
    path: Path
    rename: dict[str, str] = Field(default_factory=dict)


class WorkflowConfig(BaseModel):
    rainfall_data: RainGaugeDataConfig
    rainfall_metadata: RainGaugeMetadataConfig
    data_columns: ColumnConfig
    gridded_rainfall_data: GriddedRainfallConfig
    gridded_rainfall_col: str
    output_dir: Path
    rainfall_offset_hours: int
    n_hours: int
    verbose: bool = False
    min_n_timesteps: int = 100
    batch_size: int = 5

    def load_rainfall_data(self) -> pl.DataFrame:
        return pl.read_parquet(self.rainfall_data.path)

    def load_rainfall_metadata(self) -> pl.DataFrame:
        return pl.read_parquet(self.rainfall_metadata.path)

    def load_gridded_rainfall(self) -> xr.Dataset:
        ds = xr.open_dataset(self.gridded_rainfall_data.path)
        if self.gridded_rainfall_data.rename:
            ds = ds.rename(self.gridded_rainfall_data.rename)
        assert self.rainfall_col in ds.data_vars, (
            f"{self.rainfall_col} not in gridded_rainfall_data"
        )
        return ds
