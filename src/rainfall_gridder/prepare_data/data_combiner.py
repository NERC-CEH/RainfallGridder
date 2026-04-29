import datetime
from pathlib import Path

import polars as pl


def build_output_path(
    base_dir: Path,
    id_col_name: str,
    station_id: str,
    suffix: str = ".parquet",
) -> Path:
    """
    TODO: does the file_path need start and end date?
    """
    if not isinstance(base_dir, Path):
        base_dir = Path(base_dir)
    return base_dir / f"{id_col_name}={station_id}" / f"*{suffix}"


def calculate_change_points(
    stations_in_same_location: pl.DataFrame,
    station_id_col: str,
    start_date_col: str = "start_date",
    end_date_col: str = "end_date",
) -> pl.DataFrame:
    """
    Calculate points at which stations record overlap in time and then create a summary of which satations are active when.

    Parameters
    ----------
    stations_in_same_location:
        Stations in same geographic location
    station_id_col:
        Name of station ID column
    start_date_col:
        Name of start date column
    end_date_col:
        Name of end date column

    Returns
    -------
    change_points_and_active_stations:
        Dataframe with the change points, start and end dates and which stations were active at that time
    """
    change_points = (
        pl.concat(
            [
                stations_in_same_location.select(pl.col(start_date_col).alias("change_point")),
                stations_in_same_location.select(pl.col(end_date_col).alias("change_point")),
            ]
        )
        .unique()
        .sort("change_point")
    )

    segments = change_points.with_columns(pl.col("change_point").shift(-1).alias("next_time")).drop_nulls()

    change_points_and_active_stations = (
        segments.join(stations_in_same_location, how="cross")
        .filter((pl.col(start_date_col) < pl.col("next_time")) & (pl.col(end_date_col) > pl.col("change_point")))
        .group_by(["change_point", "next_time"])
        .agg(pl.col(station_id_col).sort().alias("active_stations"))
        .sort("change_point")
    )

    return change_points_and_active_stations


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
        self.combined_station_col_name = self._get_combined_station_col_name(station_id_col)

    def _calculate_change_points(self):
        return calculate_change_points(self.metadata, self.station_id_col)

    def _get_combined_station_col_name(self, station_id_col):
        return "-".join(str(station_id) for station_id in sorted(self.metadata[station_id_col].unique().to_list()))

    def loop_through_and_merge_data(
        self,
        nearest_gridded_daily_cell: pl.DataFrame,
        date_time_col: str,
        rain_col: str,
        rainfall_offset_hours: int,
    ):
        combined_data = pl.DataFrame()

        for s_date, e_date, station_ids in self.change_points.iter_rows():
            station_ids_cols = [date_time_col] + station_ids

            segment_rows = self.pivoted_gauge_data.filter(pl.col(date_time_col) >= s_date).filter(
                pl.col(date_time_col) < e_date
            )[station_ids_cols]

            # Check which segmented rows line up better with daily gridded rainfall
            if len(station_ids) > 1:
                gauge_gridded_matcher = GaugeVsGriddedRainfallMatcher(
                    gauge_station_ids=station_ids,
                    output_col_name=self.combined_station_col_name,
                    rainfall_offset_hours=rainfall_offset_hours,
                    date_time_col=date_time_col,
                )

                segment_rows = gauge_gridded_matcher.run(
                    segment_rows=segment_rows,
                    nearest_gridded_daily_cell=nearest_gridded_daily_cell,
                    s_date=s_date,
                    e_date=e_date,
                    rain_col=rain_col,
                )
            else:
                segment_rows = segment_rows.rename({station_ids[0]: self.combined_station_col_name})

            combined_data = pl.concat([combined_data, segment_rows])

        return combined_data


class GaugeVsGriddedRainfallMatcher:
    def __init__(
        self,
        gauge_station_ids: list[str],
        output_col_name: str,
        rainfall_offset_hours: int,
        date_time_col: str,
    ):
        self.gauge_station_ids = gauge_station_ids
        self.output_col_name = output_col_name
        self.rainfall_offset_hours = rainfall_offset_hours
        self.date_time_col = date_time_col

    def aggregate_subdaily_to_daily(self, segment_rows: pl.DataFrame) -> pl.DataFrame:
        return segment_rows.group_by_dynamic(
            self.date_time_col,
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
        gridded_daily = nearest_gridded_daily_cell.sel(time=slice(s_date, e_date))[rain_col].to_pandas().reset_index()

        return (
            pl.from_pandas(gridded_daily)
            .with_columns(pl.col("time").cast(pl.Datetime("us")) + datetime.timedelta(hours=self.rainfall_offset_hours))
            .rename({"time": self.date_time_col})
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
            on=self.date_time_col,
        )

    def find_closest_gauge_per_day(
        self,
        df: pl.DataFrame,
        rain_col: str,
    ) -> pl.DataFrame:
        df = df.with_columns(
            pl.struct([(pl.col(c) - pl.col(rain_col)).abs().alias(c) for c in self.gauge_station_ids]).alias(
                "rainfall_diff"
            )
        )

        return df.with_columns(
            pl.col("rainfall_diff").map_elements(lambda d: min(d, key=d.get)).alias("closest_gauge")
        ).drop("rainfall_diff")

    def broadcast_daily_choice_to_subdaily(
        self,
        segment_rows: pl.DataFrame,
        daily_with_closest: pl.DataFrame,
        return_gauge_name: bool = False,
    ) -> pl.DataFrame:
        daily_with_closest = daily_with_closest.with_columns(
            pl.col(self.date_time_col).alias("interval_start"),
            (pl.col(self.date_time_col) + pl.duration(days=1)).alias("interval_end"),
        )
        joined = segment_rows.join_where(
            daily_with_closest,
            (pl.col(self.date_time_col) >= pl.col("interval_start"))
            & (pl.col(self.date_time_col) < pl.col("interval_end")),
        ).select(
            self.date_time_col,
            *self.gauge_station_ids,
            "closest_gauge",
        )
        returned_cols = [self.date_time_col, self.output_col_name]
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
