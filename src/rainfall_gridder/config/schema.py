from pathlib import Path
import polars as pl
import xarray as xr
from pydantic import BaseModel


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
    path: xr.Dataset
    rainfall_col: str


class WorkflowConfig(BaseModel):
    rainfall_data: RainGaugeDataConfig
    rainfall_metadata: RainGaugeMetadataConfig
    data_columns: ColumnConfig
    gridded_rainfall_data: GriddedRainfallConfig
    output_dir: Path
    rainfall_offset_hours: int
    n_hours: int
    verbose: bool
    min_n_timesteps: int = 100
    batch_size: int = 5

    def load_rainfall_data(self) -> pl.DataFrame:
        return pl.read_parquet(self.rainfall_data.path)

    def load_rainfall_metadata(self) -> pl.DataFrame:
        return pl.read_parquet(self.rainfall_metadata.path)

    def load_gridded_rainfall(self) -> xr.Dataset:
        ds = xr.open_dataset(self.gridded_rainfall_data.path)
        assert self.gridded_rainfall_data.rainfall_col in ds.data_vars, (
            f"{self.gridded_rainfall_data.rainfall_col} not in gridded_rainfall_data"
        )
        return ds
