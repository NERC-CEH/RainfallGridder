import polars as pl
import xarray as xr
from rainfall_gridder import prepare_data
from rainfall_gridder.utils import xarray_utils


class DataPreparer:
    def __init__(
        self,
        data: pl.DataFrame,
        metadata: pl.DataFrame,
        station_id_col: str,
        date_time_col: str,
        gridded_data: xr.Dataset,
    ):
        self.data = data
        self.station_id_col = station_id_col
        self.date_time_col = date_time_col
        self.metadata = self._prepare_metadata(metadata)
        self.gridded_data = gridded_data

    def _remove_duplicates_in_metadata(self, metadata):
        return metadata.unique(
            subset=[self.station_id_col]
        )  # TODO: this would leave wrong coords if it returns first unique

    def _prepare_metadata(self, metadata):
        metadata = self._remove_duplicates_in_metadata(metadata)
        try:
            prepare_data.metadata_preparer.add_completeness_to_metadata(
                self.data, metadata, station_id_col=self.station_id_col, date_time_col=self.date_time_col
            )
        except ValueError as ve:
            print(ve)

        return prepare_data.metadata_preparer.add_completeness_to_metadata(
            self.data, metadata, station_id_col=self.station_id_col, date_time_col=self.date_time_col
        )

    def _prepare_gridded_data(self, gridded_data):
        gridded_data = xarray_utils.replace_daily_time_step_hour_with_zero(gridded_data, self.date_time_col)
        return self
