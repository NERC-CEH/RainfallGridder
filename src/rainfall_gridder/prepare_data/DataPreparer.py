from pathlib import Path
import polars as pl
import xarray as xr
from rainfall_gridder.prepare_data import data_combiner, data_formatting, metadata_preparer
from rainfall_gridder.utils import spatial_utils, xarray_utils 


class DataPreparer:
    def __init__(
        self,
        data: pl.DataFrame,
        metadata: pl.DataFrame,
        station_id_col: str,
        station_name_col: str,
        precipitation_col: str,
        date_time_col: str,
        start_date_col: str,
        end_date_col: str,
        easting_col: str,
        northing_col: str,
        gridded_rainfall_data: xr.Dataset,
        gridded_rainfall_col: str,
        rainfall_offset_hours: int,
        output_dir: str | Path,
        verbose: bool = False,
        min_n_timesteps: int=100,
    ):
        """
        Main data preparer for gridded workflow.

        Parameters
        ----------
        gridded_rainfall_col:
            Name of rainfall variable in the gridded_rainfall_data
        rainfall_offset_hours:
            First hour of the rainfall day (e.g. 9 if running from 9am to 8.59am)
        output_dir:
            Output directory for data files
        
        """
        self.station_id_col = station_id_col
        self.station_name_col = station_name_col
        self.precipitation_col = precipitation_col
        self.date_time_col = date_time_col
        self.start_date_col = start_date_col
        self.end_date_col = end_date_col
        self.easting_col = easting_col
        self.northing_col = northing_col
        self.rainfall_offset_hours = rainfall_offset_hours
        self.output_dir = output_dir
        self.verbose = verbose
        self.min_n_timesteps = min_n_timesteps
        self.gridded_rainfall_col = gridded_rainfall_col

        # Prepare data inputs
        self.data = self._prepare_data(data)
        self.metadata = self._prepare_metadata(metadata)
        self.gridded_rainfall_data = self._prepare_gridded_rainfall_data(gridded_rainfall_data)
        
        # empty final outputs
        self.prepared_data = None
        self.prepared_metadata = None

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

    def _prepare_gridded_rainfall_data(self, gridded_rainfall_data):
        gridded_rainfall_data = xarray_utils.replace_daily_time_step_hour_with_zero(gridded_rainfall_data, self.date_time_col)
        gridded_rainfall_data = xarray_utils.subset_gridded_data_to_metadata_bounds(
            gridded_rainfall_data, self.metadata, self.easting_col, self.northing_col
        )
        return gridded_rainfall_data

    def _prepare_data(self):
        return data_formatting.set_negative_precip_values_to_none(self.data, precip_col=self.precipitation_col)

    @classmethod
    def run(cls, partition_by_columns: list=None, **kwargs):
        data_preparer = cls(**kwargs)
        if data_preparer.verbose:
            print("Preparing data for gridder")
        data_preparer.prepare_data_and_metadata_for_gridding()
        if data_preparer.verbose:
            print(f"Saving data to {cls.output_dir}")
        data_preparer.save_prepared_data(partition_by_columns)
        data_preparer.save_prepared_metadata()

    def prepare_data_and_metadata_for_gridding(self):
        metadata_cols_to_check_identical = [self.easting_col, self.northing_col, "station_group_id", "file_path"]
        metadata_cols_to_combine = [self.station_id_col, self.station_name_col]

        final_gauge_data_list = []
        final_station_metadata_list = []
        column_order = [self.date_time_col, self.precipitation_col, self.station_id_col]
        metadata_column_order = self.metadata.columns

        for station_group_id in self.metadata['station_group_id'].unique():
            metadata_one_group = self.metadata.filter(pl.col("station_group_id") == station_group_id)
            data_one_group = self.data.filter(pl.col(self.station_id_col).is_in(metadata_one_group[self.station_id_col].unique().to_list()))

            # Sort and drop duplicates
            data_one_group = data_one_group.sort(self.date_time_col).unique()
            
            if len(data_one_group[self.station_id_col].unique()) > 1:
                print(station_group_id, len(data_one_group[self.station_id_col].unique()))
                # if duplicate exist, merge segments
                # create pivot of data
                data_one_group_pivot = data_one_group.pivot(
                    values=self.precipitation_col, index=self.date_time_col, on=self.station_id_col
                ).sort(by=self.date_time_col)

                gauge_combiner = data_combiner.RainGaugeSegmentCombiner(
                    pivoted_gauge_data=data_one_group_pivot,
                    metadata=metadata_one_group,
                    station_id_col=self.station_id_col,
                )
                nearest_gear_daily_cell = spatial_utils.get_nearest_grid_cell(self.gridded_rainfall_data, easting=metadata_one_group[self.easting_col][0], northing=metadata_one_group[self.easting_col][0])
                combined_data = gauge_combiner.loop_through_and_merge_data(nearest_gear_daily_cell,
                                                                        date_time_col=self.date_time_col,
                                                                        rain_col=self.gridded_rainfall_col,
                                                                        rainfall_offset_hours=self.rainfall_offset_hours)
                station_name = gauge_combiner.combined_station_col_name

                # unpivot data
                data_one_group = combined_data.unpivot(
                    index=[self.date_time_col],
                    on=[station_name],
                    variable_name=self.station_id_col,
                    value_name=self.precipitation_col
                )
                
            else:
                station_name = metadata_one_group[self.station_id_col][0]

            # Save data if at least N months worth of non-null record
            if len(data_one_group.drop_nulls()) >= self.min_n_timesteps:
                if self.verbose:
                    print(f'Adding group ID: {station_group_id}')
                output_file_name = str(data_combiner.build_output_path(base_dir=self.output_dir / "data", id_col_name=self.station_id_col, station_id=station_name))
                metadata_one_group = metadata_one_group.with_columns(pl.lit(output_file_name).alias("file_path"))
                data_one_group = data_one_group.select(column_order)
                final_gauge_data_list.append(data_one_group)
            else:
                if self.verbose:
                    print(f"{station_name} being ignored as not more than {self.min_n_timesteps} time steps.")
            if len(metadata_one_group) > 1:
                if self.verbose:
                    print(f"merging metadata of {station_name}")
                metadata_merger = metadata_preparer.MetadataMerger(metadata=metadata_one_group,
                                                cols_to_check_identical=metadata_cols_to_check_identical,
                                                cols_to_combine=metadata_cols_to_combine,
                                                start_date_col=self.start_date_col,
                                                end_date_col=self.end_date_col,
                                                )
                merged_metadata = metadata_merger.merge_group_metadata(group_name=station_name,
                                                            group_name_col=self.station_id_col,
                                                            min_datetime=data_one_group[self.date_time_col].min(),
                                                            max_datetime=data_one_group[self.date_time_col].max(),
                                                            )
                final_station_metadata_list.append(merged_metadata.select(metadata_column_order))
            else:
                final_station_metadata_list.append(metadata_one_group.select(metadata_column_order))
        self.prepared_data = pl.concat(final_gauge_data_list)
        self.prepared_metadata = pl.concat(final_station_metadata_list, how="diagonal_relaxed")

    def save_prepared_data(self, partition_by_columns: list = None) -> None:
        """
        Save data that has been prepared for gridding.

        Parameters
        ----------
        partition_by_columns:
            Columns that decide the partitioning of the output parquet file structure (default is station_id_col)
        """
        if partition_by_columns is None:
            partition_by_columns = [self.station_id_col]
        
        if self.prepared_data is None:
            raise RuntimeError("You must call prepare_data_and_metadata_for_gridding() before save_output()")
        
        assert len(self.prepared_metadata.filter(pl.col('file_path').is_duplicated())) == 0, "Problem with metadata as duplicate filepaths"

        # Save partitioned parquet file
        (
            self.prepared_data
            .sort(self.date_time_col)
            .write_parquet(
                self.output_dir / "data",
                partition_by=partition_by_columns,
            )
        )
        if self.verbose:
            print(f"output available at: {self.output_dir / "data/"}")

    def save_prepared_metadata(self) -> None:
        if self.prepared_metadata is None:
            raise RuntimeError("You must call prepare_data_and_metadata_for_gridding() before save_final_metadata()")
        self.prepared_metadata.write_parquet(self.output_dir / "prepared_metadata.parquet")
        if self.verbose:
            print(f"output available at: {self.output_dir / "prepared_metadata.parquet"}") 
