import datetime
from pathlib import Path
import polars as pl
import xarray as xr
import scipy.stats

HYDROLOGICAL_DAY_START_HOUR = 10 # hours, default 10-9 am
NEAREST_GRID_CELL_TOLERANCE_M = 1000  # metres


def check_col_content_is_identical(metadata, col):
    assert len(metadata[col].unique()) == 1, (
        f"Not all values in {col} are identical: '{metadata[col].unique()}'"
    )


def combine_metadata_col_contents(metadata, col):
    return "-".join(str(row_val) for row_val in metadata[col].unique().to_list())


class MetadataMerger:
    def __init__(
        self,
        metadata: pl.DataFrame,
        cols_to_check_identical: list,
        cols_to_combine: list,
        start_date_col: str,
        end_date_col: str,
    ):
        self.metadata = metadata
        self.cols_to_combine = cols_to_combine
        self.cols_to_check_identical = cols_to_check_identical
        self.start_date_col = start_date_col
        self.end_date_col = end_date_col
        self._check_for_identical_values_in_col()

    def _check_for_identical_values_in_col(self):
        for col in self.cols_to_check_identical:
            check_col_content_is_identical(self.metadata, col)

    def merge_group_metadata(
        self, group_name, group_name_col, min_datetime, max_datetime, completeness_col
    ):
        combined_data = {}
        combined_data[group_name_col] = group_name
        for col in self.cols_to_combine:
            combined_data[col] = combine_metadata_col_contents(self.metadata, col)
        for col in self.cols_to_check_identical:
            combined_data[col] = self.metadata[col][0]

        combined_data[self.start_date_col] = min_datetime
        combined_data[self.end_date_col] = max_datetime
        combined_data[completeness_col] = None  # Temporary workaround

        # Fill in missing columns with None
        for col in self.metadata.columns:
            if col not in combined_data.keys():
                try:
                    check_col_content_is_identical(self.metadata, col)
                    combined_data[col] = self.metadata[col][0]
                except AssertionError as ae:
                    combined_data[col] = None

        return pl.DataFrame(combined_data)


def build_output_path(
    base_dir: Path,
    id_col_name: str,
    station_id: str,
    suffix: str = ".parquet",
) -> Path:
    """
    TODO: does the file_path need start and end date?
    """
    return base_dir / f"{id_col_name}={station_id}/data*{suffix}"


def calculate_change_points(stations_in_same_location: pl.DataFrame, station_id_col: str) -> pl.DataFrame:
    change_points = (
        pl.concat(
            [
                stations_in_same_location.select(
                    pl.col("START_DATE").alias("change_point")
                ),
                stations_in_same_location.select(
                    pl.col("END_DATE").alias("change_point")
                ),
            ]
        )
        .unique()
        .sort("change_point")
    )

    segments = change_points.with_columns(
        pl.col("change_point").shift(-1).alias("next_time")
    ).drop_nulls()

    change_points_and_active_stations = (
        segments.join(stations_in_same_location, how="cross")
        .filter(
            (pl.col("START_DATE") < pl.col("next_time"))
            & (pl.col("END_DATE") > pl.col("change_point"))
        )
        .group_by(["change_point", "next_time"])
        .agg(pl.col(station_id_col).sort().alias("active_stations"))
        .sort("change_point")
    )

    return change_points_and_active_stations


def get_nearest_rain_grid_cell(
    rain_data: xr.Dataset,
    easting: int | float,
    northing: int | float,
    tolerance=NEAREST_GRID_CELL_TOLERANCE_M,
) -> xr.Dataset:
    # Should this select the 2*2 grid cells surrounding (in case on edge of a single cell)?
    return rain_data.sel(
        x=easting,
        y=northing,
        method="nearest",
        tolerance=tolerance,
    )


class RainGaugeSegmentCombiner:
    def __init__(
        self,
        pivoted_gauge_data: pl.DataFrame,
        metadata: pl.DataFrame,
        station_id_col: str,
    ):
        self.pivoted_gauge_data = pivoted_gauge_data
        self.metadata = metadata
        self.station_id_col = station_id_col
        self.change_points = self._calculate_change_points()
        self.combined_station_col_name = self._get_combined_station_col_name(
            station_id_col
        )

    def _calculate_change_points(self):
        return calculate_change_points(self.metadata, self.station_id_col)

    def _get_combined_station_col_name(self, station_id_col):
        return "-".join(
            str(int(station_id))
            for station_id in self.metadata[station_id_col].unique().to_list()
        )

    def _convert_station_ids_to_str(self, station_ids):
        """
        Converts a list or iterable of station IDs (floats/ints) to strings.
        """
        return [str(int(s_id)) for s_id in station_ids]

    def loop_through_and_merge_data(
        self,
        nearest_gridded_daily_cell: pl.DataFrame,
        date_time_col: str,
        rain_col: str,
        rainfall_offset_hours: int,
    ):
        combined_data = pl.DataFrame()

        for s_date, e_date, station_ids in self.change_points.iter_rows():
            station_ids = self._convert_station_ids_to_str(station_ids)
            station_ids_cols = [date_time_col] + station_ids

            segment_rows = self.pivoted_gauge_data.filter(
                pl.col(date_time_col) >= s_date
            ).filter(pl.col(date_time_col) < e_date)[station_ids_cols]

            # Check which segmented rows line up better with daily gridded rainfall
            if len(station_ids) > 1:
                gauge_gridded_matcher = GaugeVsGriddedRainfallMatcher(
                    gauge_station_ids=station_ids,
                    output_col_name=self.combined_station_col_name,
                    rainfall_offset_hours=rainfall_offset_hours,
                )

                segment_rows = gauge_gridded_matcher.run(
                    segment_rows=segment_rows,
                    nearest_gridded_daily_cell=nearest_gridded_daily_cell,
                    s_date=s_date,
                    e_date=e_date,
                    rain_col=rain_col,
                )
            else:
                segment_rows = segment_rows.rename(
                    {station_ids[0]: self.combined_station_col_name}
                )

            combined_data = pl.concat([combined_data, segment_rows])

        return combined_data


class GaugeVsGriddedRainfallMatcher:
    def __init__(
        self,
        gauge_station_ids: list[str],
        output_col_name: str,
        rainfall_offset_hours: int,
    ):
        self.gauge_station_ids = gauge_station_ids
        self.output_col_name = output_col_name
        self.rainfall_offset_hours = rainfall_offset_hours

    def aggregate_subdaily_to_daily(self, segment_rows: pl.DataFrame) -> pl.DataFrame:
        return segment_rows.group_by_dynamic(
            "DATE_TIME",
            every="1d",
            offset=f"{self.rainfall_offset_hours}h",
        ).agg(pl.sum(c).alias(c) for c in self.gauge_station_ids)

    def prepare_gridded_daily(
        self,
        nearest_gridded_daily_cell: pl.DataFrame,
        s_date: datetime.datetime,
        e_date: datetime.datetime,
        rain_col: str,
    ) -> pl.DataFrame:
        gridded_daily = (
            nearest_gridded_daily_cell.sel(time=slice(s_date, e_date))[rain_col]
            .to_pandas()
            .reset_index()
        )

        return (
            pl.from_pandas(gridded_daily)
            .with_columns(
                pl.col("time").cast(pl.Datetime("us"))
                + datetime.timedelta(hours=self.rainfall_offset_hours)
            )
            .rename({"time": "DATE_TIME"})
        )

    def join_daily_gauge_and_gridded(
        self,
        segment_rows_daily: pl.DataFrame,
        gridded_daily: pl.DataFrame,
    ) -> pl.DataFrame:
        """
        Join daily gauge totals with daily gridded rainfall
        """
        return segment_rows_daily.join(
            gridded_daily,
            on="DATE_TIME",
        )

    def find_closest_gauge_per_day(
        self,
        df: pl.DataFrame,
        rain_col: str,
    ) -> pl.DataFrame:
        df = df.with_columns(
            pl.struct(
                [
                    (pl.col(c) - pl.col(rain_col)).abs().alias(c)
                    for c in self.gauge_station_ids
                ]
            ).alias("rainfall_diff")
        )

        return df.with_columns(
            pl.col("rainfall_diff")
            .map_elements(lambda d: min(d, key=d.get))
            .alias("closest_gauge")
        ).drop("rainfall_diff")

    def broadcast_daily_choice_to_subdaily(
        self,
        segment_rows: pl.DataFrame,
        daily_with_closest: pl.DataFrame,
        return_gauge_name: bool = False,
    ) -> pl.DataFrame:
        daily_with_closest = daily_with_closest.with_columns(
            pl.col("DATE_TIME").alias("interval_start"),
            (pl.col("DATE_TIME") + pl.duration(days=1)).alias("interval_end"),
        )
        ## OLD MEMORY INTENSIVE JOIN
        # joined = (
        #     segment_rows.join(daily_with_closest, how="cross")
        #     .filter(
        #         (pl.col("DATE_TIME") >= pl.col("interval_start"))
        #         & (pl.col("DATE_TIME") < pl.col("interval_end"))
        #     )
        #     .select(
        #         "DATE_TIME",
        #         *self.gauge_station_ids,
        #         "closest_gauge",
        #     )
        # )
        joined = segment_rows.join_where(
            daily_with_closest,
            (pl.col("DATE_TIME") >= pl.col("interval_start"))
            & (pl.col("DATE_TIME") < pl.col("interval_end")),
        ).select(
            "DATE_TIME",
            *self.gauge_station_ids,
            "closest_gauge",
        )
        returned_cols = ["DATE_TIME", self.output_col_name]
        if return_gauge_name:
            returned_cols += ["closest_gauge"]
        return joined.with_columns(
            pl.struct(self.gauge_station_ids + ["closest_gauge"])
            .map_elements(
                lambda s: s[s["closest_gauge"]],
                return_dtype=pl.Float64,
            )
            .alias(self.output_col_name)
        ).select(returned_cols)

    def run(
        self,
        segment_rows: pl.DataFrame,
        nearest_gridded_daily_cell: pl.DataFrame,
        s_date: datetime.datetime,
        e_date: datetime.datetime,
        rain_col: str,
        return_gauge_name: bool = False,
    ) -> pl.DataFrame:
        daily_gauge = self.aggregate_subdaily_to_daily(segment_rows)
        gridded_daily = self.prepare_gridded_daily(
            nearest_gridded_daily_cell,
            s_date,
            e_date,
            rain_col,
        )
        daily_joined = self.join_daily_gauge_and_gridded(
            daily_gauge,
            gridded_daily,
        )
        daily_with_closest = self.find_closest_gauge_per_day(daily_joined, rain_col)
        return self.broadcast_daily_choice_to_subdaily(
            segment_rows,
            daily_with_closest,
            return_gauge_name,
        )


class GaugeVsGriddedCombiner:
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
        self.gauge_data = gauge_data.filter(pl.col(station_id_col) == station_id).sort(
            by=gauge_data_time_col
        )
        self.gauge_metadata = metadata.filter(pl.col(station_id_col) == station_id)
        self.nearest_gridded_daily = get_nearest_rain_grid_cell(
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
                label='left',
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
