import polars as pl
from rainfallqc.utils import neighbourhood_utils


class NearbyGaugeDataLoader:
    def __init__(
        self,
        metadata: pl.DataFrame,
        station_id: str,
        start_datetime_col: str,
        end_datetime_col: str,
        station_id_col: str,
        min_overlap_days: int,
        distance_threshold: int = 50,
        n_closest: int = 10,
    ):
        self.station_id = station_id
        self.start_datetime_col = start_datetime_col
        self.end_datetime_col = end_datetime_col
        self.station_id_col = station_id_col
        self.distance_threshold = distance_threshold
        self.min_overlap_days = min_overlap_days
        self.n_closest = n_closest

        self.nearby_metadata = self._get_nearby_metadata(metadata)
        self.nearby_gauge_distances = self._get_nearby_gauge_distances()

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

    def _get_nearby_gauge_distances(self):
        return neighbourhood_utils.compute_km_distances_from_target_id(
            self.nearby_metadata,
            target_id=self.station_id,
            station_id_col=self.station_id_col,
        )

    def load_nearby_gauge_data_from_parquet_files(self, path_to_files):
        stations_to_load = self.nearby_metadata[self.station_id_col].unique().to_list()
        nearby_rainfall_data = (
            pl.scan_parquet(path_to_files)
            .filter(pl.col(self.station_id_col).cast(pl.String).is_in(stations_to_load))
            .collect()
        )
        return nearby_rainfall_data

    def load_nearby_gauge_data_from_csv_files(self, path_to_files):
        stations_to_load = self.nearby_metadata[self.station_id_col].unique().to_list()
        nearby_rainfall_data = (
            pl.scan_csv(path_to_files)
            .filter(pl.col(self.station_id_col).cast(pl.String).is_in(stations_to_load))
            .collect()
        )
        return nearby_rainfall_data
