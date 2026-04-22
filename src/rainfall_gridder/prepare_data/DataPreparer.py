import polars as pl
import xarray as xr
from rainfall_gridder.prepare_data import data_formatting, metadata_preparer
from rainfall_gridder.utils import xarray_utils


class DataPreparer:
    def __init__(
        self,
        data: pl.DataFrame,
        metadata: pl.DataFrame,
        station_id_col: str,
        precipitation_col: str,
        date_time_col: str,
        easting_col: str,
        northing_col: str,
        gridded_data: xr.Dataset,
    ):
        self.data = data
        self.station_id_col = station_id_col
        self.precipitation_col = precipitation_col
        self.date_time_col = date_time_col
        self.easting_col = easting_col
        self.northing_col = northing_col
        self.metadata = self._prepare_metadata(metadata)
        self.gridded_data = gridded_data

    def _remove_duplicates_in_metadata(self, metadata):
        
        return metadata.unique(
            subset=[self.station_id_col]
        )  # TODO: this would leave wrong coords if it returns first unique

    def _prepare_metadata(self, metadata):
        metadata = self._remove_duplicates_in_metadata(metadata)
        try:
            metadata_preparer.add_completeness_to_metadata(
                self.data, metadata, station_id_col=self.station_id_col, date_time_col=self.date_time_col
            )
        except ValueError as ve:
            print(ve)

        metadata = metadata_preparer.add_completeness_to_metadata(
            self.data, metadata, station_id_col=self.station_id_col, date_time_col=self.date_time_col
        )
        metadata = data_formatting.group_metadata_by_station_locations(metadata, easting_col=self.easting_col, northing_col=self.northing_col)
        return data_formatting.add_blank_file_path_to_metadata(metadata)

    def _prepare_gridded_data(self, gridded_data):
        gridded_data = xarray_utils.replace_daily_time_step_hour_with_zero(gridded_data, self.date_time_col)
        gridded_data = xarray_utils.subset_gridded_data_to_metadata_bounds(gridded_data, self.metadata, self.easting_col, self.northing_col)
        return gridded_data
    
    def _prepare_data(self):
        return data_formatting.set_negative_precip_values_to_none(self.data, precip_col=self.precipitation_col)
