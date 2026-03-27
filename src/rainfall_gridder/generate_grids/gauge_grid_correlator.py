import polars as pl
import xarray as xr
import scipy.stats

from rainfall_gridder.prepare_data.metadata_preparer import GaugeVsGriddedRainfallMatcher
from rainfall_gridder.utils import get_nearest_grid_cell


class GaugeVsGriddedCorrelator:
    def __init__(
        self,
        gauge_data: pl.DataFrame,
        metadata: pl.DataFrame,
        nearest_gridded_daily: xr.Dataset,
        station_id: str,
        gauge_data_col: str,
        gridded_data_col: str,
        start_datetime_col: str,
        end_datetime_col: str,
        station_id_col: str,
        rainfall_offset_hours: int,
        gauge_data_time_col: str = "DATE_TIME",
        aggregate_gauge_to_daily: bool = True,
    ):
        """
        TODO: make sure the combining of gauge name is done in order i.e. 1-2 not 2-1
        """
        # filter to the single station ID
        self.gauge_data = gauge_data.filter(pl.col(station_id_col) == station_id).sort(by=gauge_data_time_col)
        self.gauge_metadata = metadata.filter(pl.col(station_id_col) == station_id)
        self.nearest_gridded_daily = get_nearest_grid_cell(
            nearest_gridded_daily,
            easting=self.gauge_metadata["EASTING"][0],
            northing=self.gauge_metadata["NORTHING"][0],
        )
        self.station_id = station_id
        self.gauge_data_col = gauge_data_col
        self.gridded_data_col = gridded_data_col
        self.start_datetime_col = start_datetime_col
        self.end_datetime_col = end_datetime_col
        self.station_id_col = station_id_col
        self.gauge_data_time_col = gauge_data_time_col
        self.rainfall_offset_hours = rainfall_offset_hours
        if aggregate_gauge_to_daily:
            self.gauge_data = self._aggregate_gauge_subdaily_to_daily()
        self.combined_data = self._join_gauge_to_grid()

    def _aggregate_gauge_subdaily_to_daily(self) -> pl.DataFrame:
        return (
            self.gauge_data.drop_nulls()
            .group_by_dynamic(
                "DATE_TIME",
                every="1d",
                offset=f"{self.rainfall_offset_hours}h",
                label="left",
            )
            .agg(pl.col(self.gauge_data_col).sum())
        )

    def _join_gauge_to_grid(self):
        s_date = self.gauge_metadata[self.start_datetime_col][0]
        e_date = self.gauge_metadata[self.end_datetime_col][0]
        gauge_gridded_matcher = GaugeVsGriddedRainfallMatcher(
            [self.gauge_data_col], output_col_name="", rainfall_offset_hours=self.rainfall_offset_hours
        )
        nearest_gridded_daily_cell_df = gauge_gridded_matcher.prepare_gridded_daily(
            self.nearest_gridded_daily,
            s_date=s_date,
            e_date=e_date,
            rain_col=self.gridded_data_col,
        )
        combined_gauge_gridded = gauge_gridded_matcher.join_daily_gauge_and_gridded(
            self.gauge_data, nearest_gridded_daily_cell_df
        )
        return combined_gauge_gridded

    def get_corr(self):
        r_result = scipy.stats.pearsonr(
            self.combined_data[self.gauge_data_col],
            self.combined_data[self.gridded_data_col],
        ).statistic
        rho_result = scipy.stats.spearmanr(
            self.combined_data[self.gauge_data_col],
            self.combined_data[self.gridded_data_col],
        ).statistic
        return r_result, rho_result
