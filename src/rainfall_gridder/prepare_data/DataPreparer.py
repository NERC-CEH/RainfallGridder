from pathlib import Path
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
        station_name_col: str,
        precipitation_col: str,
        date_time_col: str,
        easting_col: str,
        northing_col: str,
        gridded_data: xr.Dataset,
        verbose: bool = False,
    ):
        self.data = data
        self.station_id_col = station_id_col
        self.station_name_col = station_name_col
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
        metadata = data_formatting.group_metadata_by_station_locations(
            metadata, easting_col=self.easting_col, northing_col=self.northing_col
        )
        return data_formatting.add_blank_file_path_to_metadata(metadata)

    def _prepare_gridded_data(self, gridded_data):
        gridded_data = xarray_utils.replace_daily_time_step_hour_with_zero(gridded_data, self.date_time_col)
        gridded_data = xarray_utils.subset_gridded_data_to_metadata_bounds(
            gridded_data, self.metadata, self.easting_col, self.northing_col
        )
        return gridded_data

    def _prepare_data(self):
        return data_formatting.set_negative_precip_values_to_none(self.data, precip_col=self.precipitation_col)

    def loop_through_and_make_final_data_and_metadata(self):
        metadata_cols_to_check_identical = [self.easting_col, self.northing_col, "station_group_id", "file_path"]
        metadata_cols_to_combine = [self.station_id_col, self.station_name_col]

    def save_final_data(self, output_dir: str | Path, partition_by_columns: list = None) -> None:
        """
        Save data that has been prepared for gridding.

        Parameters
        ----------
        output_dir:
            Output directory for data files
        partition_by_columns:
            Columns that decide the partitioning of the output parquet file structure (default is station_id_col)
        """
        if not partition_by_columns:
            partition_by_columns = [self.station_id_col]
        # final_gauge_data = pl.concat(self.final_gauge_data_list)
        # (
        #     final_gauge_data
        #     .sort(DATE_TIME_COL)
        #     .write_parquet(
        #         output_dir / "data",
        #         partition_by=partition_by_columns,
        #         overwrite=True
        #     )
        # )
        # if self.verbose:
        #     print(f"output available at: {output_dir / "data"}")
        pass

    def save_final_metadata(self, output_dir: str | Path) -> None:
        # final_station_metadata_df = pl.concat(final_station_metadata_list, how="diagonal_relaxed")
        # assert len(final_station_metadata_df.filter(pl.col('file_path').is_duplicated())) == 0
        # final_station_metadata_df.write_parquet('outputs/example_outputs_metadata.parquet')
        pass
