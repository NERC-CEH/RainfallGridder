import polars as pl
import rainfallqc

from rainfall_gridder.utils import spatial_utils


time_res_to_n_time_steps_in_day = {"15m": 96, "1h": 24}


class QualityController:
    """
    Main quality control running algorithm.
    """

    def __init__(
        self,
        rainfall_data: pl.DataFrame,
        rainfall_metadata: pl.DataFrame,
        station_id_col: str,
        station_name_col: str,
        easting_col: str,
        northing_col: str,
        start_date_col: str,
        end_date_col: str,
        input_crs: str,
        min_n_timesteps: int,
        time_res: str,
    ):
        """
        Quality control part of gridded workflow.

        Parameters
        ----------
        rainfall_data:
            Rainfall gauge data
        rainfall_metadata:
            Details of rain gauge data
        input_crs:
            Projection of the east_west and north_south cols of the input data
        min_n_timesteps:
            Minimum number of timesteps needed in rainfall_data to be considered valid
        time_res:
            Resolution of data (i.e. hourly or 15 min denoted: '1h' or '15m')

        Returns
        -------
        """
        self.station_id_col = station_id_col
        self.station_name_col = station_name_col
        self.easting_col = easting_col
        self.northing_col = northing_col
        self.start_date_col = start_date_col
        self.end_date_col = end_date_col
        self.input_crs = self._validate_input_crs(input_crs)
        self.min_n_timesteps = min_n_timesteps
        self.time_res = self._validate_time_res(time_res)

        if "latitude" not in rainfall_data.columns or "longitude" not in rainfall_data.columns:
            self.rainfall_data = self._add_latlon_to_rainfall_data(rainfall_data)
        else:
            self.rainfall_data = rainfall_data
        self.rainfall_metadata = rainfall_metadata

    def _add_latlon_to_rainfall_data(self, rainfall_data):
        return spatial_utils.crs_to_crs(
            rainfall_data,
            crs_in=self.input_crs,
            crs_out="EPSG:4326",
            east_west_col_in=self.easting_col,
            north_south_col_in=self.northing_col,
            east_west_col_out="latitude",
            north_south_col_out="longitude",
        )

    def _validate_input_crs(self, input_crs: str) -> str:
        assert input_crs.startswith("EPSG:"), (
            f"Invalid input_crs {input_crs}, needs to begin with 'EPSG:' like 'EPSG:4326'."
        )
        return input_crs

    def _validate_time_res(self, time_res: str) -> str:
        assert time_res in time_res_to_n_time_steps_in_day.keys(), (
            f"'{time_res}' not in accepted time resolutions for data. Accepted time res: {time_res_to_n_time_steps_in_day.keys()}"
        )
        return time_res

    def get_ten_nearest_neighbour_ids(self, target_station_id: str, distance_threshold_km: int = 50):
        return rainfallqc.neighbourhood_utils.get_ids_of_n_nearest_overlapping_neighbouring_gauges(
            self.rainfall_metadata,
            target_id=target_station_id,
            distance_threshold=distance_threshold_km,  # in km
            min_overlap_days=self.min_n_timesteps,  # in days
            n_closest=10,  # number of neighbours to return
            station_id_col=self.station_id_col,
            start_datetime_col=self.start_date_col,
            end_datetime_col=self.end_date_col,
        )
