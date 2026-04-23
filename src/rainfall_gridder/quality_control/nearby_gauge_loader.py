from pathlib import Path
import polars as pl
from rainfallqc.utils import neighbourhood_utils


class NearbyRainfallDataLoader:
    def __init__(
        self,
        metadata: pl.DataFrame,
        rainfall_data_source: str,
        station_id: str,
        date_time_col: str,
        start_datetime_col: str,
        end_datetime_col: str,
        station_id_col: str,
        min_overlap_days: int,
        time_res: str,
        path_to_rainfall_files: None = None,
        rainfall_data_pl: None = None,
        distance_threshold: int = 50,
        n_closest: int = 10,
    ):
        """
        Loader for nearby rain gauge stations.

        Parameters
        ----------
        rainfall_data_source:
            Source for the rainfall data, can be either 'csv', 'parquet' for file_paths or 'df' for a loaded in polars df
        time_res:
            Resolution of data (i.e. hourly or 15 min denoted: '1h' or '15m')

        """

        self.rainfall_data_source = rainfall_data_source
        self.station_id = station_id
        self.date_time_col = date_time_col
        self.start_datetime_col = start_datetime_col
        self.end_datetime_col = end_datetime_col
        self.station_id_col = station_id_col
        self.distance_threshold = distance_threshold
        self.min_overlap_days = min_overlap_days
        self.n_closest = n_closest
        self.time_res = time_res

        self.path_to_rainfall_files = path_to_rainfall_files
        self.rainfall_data_pl = rainfall_data_pl

        self.nearby_metadata = self._get_nearby_metadata(metadata)
        self.nearby_rain_gauge_distances = self._get_nearby_rain_gauge_distances()
        self.stations_to_load = self.nearby_metadata[self.station_id_col].unique().to_list()
        self.nearby_rainfall_data = self.load_nearby_rainfall_data()
        self.nearby_rainfall_for_rainfallqc = self.prepare_nearby_rainfall_data_for_rainfallqc()

    def _get_nearby_metadata(self, metadata):
        ten_nearest_neighbour_ids = neighbourhood_utils.get_ids_of_n_nearest_overlapping_neighbouring_gauges(
            metadata,
            target_id=self.station_id,
            station_id_col=self.station_id_col,
            distance_threshold=self.distance_threshold,
            min_overlap_days=self.min_overlap_days,
            n_closest=self.n_closest,
            start_datetime_col=self.start_datetime_col,
            end_datetime_col=self.end_datetime_col,
        )

        return metadata.filter(
            (pl.col(self.station_id_col).is_in(ten_nearest_neighbour_ids))
            | (pl.col(self.station_id_col) == self.station_id)
        )

    def _get_nearby_rain_gauge_distances(self):
        return neighbourhood_utils.compute_km_distances_from_target_id(
            self.nearby_metadata,
            target_id=self.station_id,
            station_id_col=self.station_id_col,
        )

    def load_nearby_rainfall_data(self) -> pl.DataFrame:
        if self.rainfall_data_source == "parquet":
            if self.path_to_rainfall_files is None:
                raise ValueError("path_to_files must be provided for parquet data source")
            nearby_rainfall_data = self._load_nearby_rainfall_data_from_parquet_files()

        elif self.rainfall_data_source == "csv":
            if self.path_to_rainfall_files is None:
                raise ValueError("path_to_files must be provided for csv data source")
            nearby_rainfall_data = self._load_nearby_rainfall_data_from_csv_files()

        elif self.rainfall_data_source == "df":
            if self.rainfall_data_pl is None:
                raise ValueError("rainfall_data must be provided for df data source")
            nearby_rainfall_data = self._load_nearby_rainfall_data_from_pl()
        else:
            raise ValueError(
                f"Unsupported data_source: {self.data_source}. Please set this to either 'parquet', 'csv', or 'df' if you have a polars dataframe."
            )
        
        return self._rename_and_sort_rainfall_data_by_time()

    def _load_nearby_rainfall_data_from_parquet_files(self) -> pl.DataFrame:
        nearby_rainfall_data = (
            pl.scan_parquet(self.path_to_rainfall_files)
            .filter(pl.col(self.station_id_col).cast(pl.String).is_in(self.stations_to_load))
            .collect()
        )
        return nearby_rainfall_data

    def _load_nearby_rainfall_data_from_csv_files(self) -> pl.DataFrame:
        nearby_rainfall_data = (
            pl.scan_csv(self.path_to_rainfall_files)
            .filter(pl.col(self.station_id_col).cast(pl.String).is_in(self.stations_to_load))
            .collect()
        )
        return nearby_rainfall_data

    def _load_nearby_rainfall_data_from_pl(self) -> pl.DataFrame:
        return self.rainfall_data_pl.filter(pl.col(self.station_id_col).cast(pl.String).is_in(self.stations_to_load))

    def _rename_and_sort_rainfall_data_by_time(self) -> pl.DataFrame:
        return self.nearby_rainfall_data.rename({self.date_time_col: "time"}).sort(by="time")

    def prepare_nearby_rainfall_data_for_rainfallqc(self):
        nearby_rainfall_data_pivot = self.pivot_nearby_rainfall_data(self.nearby_rainfall_data)
        nearby_rainfall_for_rainfallqc = self.upsample_nearby_rainfall_data(nearby_rainfall_data_pivot)
        return nearby_rainfall_for_rainfallqc

    def pivot_nearby_rainfall_data(self) -> pl.DataFrame:
        return self.nearby_rainfall_data.pivot(
            values=self.precipitation_col, index=self.date_time_col, on=self.station_id_col
        )

    def upsample_nearby_rainfall_data(self) -> pl.DataFrame:
        return self.nearby_rainfall_pivot_data.upsample("time", every=self.time_res)
