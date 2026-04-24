from pathlib import Path
import polars as pl
import rainfallqc

from rainfall_gridder.quality_control.nearby_gauge_loader import NearbyRainfallDataLoader
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
        date_time_col: str,
        precipitation_col: str,
        easting_col: str,
        northing_col: str,
        start_date_col: str,
        end_date_col: str,
        input_crs: str,
        min_n_timesteps: int,
        output_dir: str | Path,
        time_res: str,
        smallest_rainfall_amount: int | float,
        min_n_neighbours: int,
        qc_framework: str,
        nearby_rainfall_data_loader_kwargs: dict = {},
        verbose: bool = False,
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
        output_dir:
            Output directory for data files
        min_n_timesteps:
            Minimum number of timesteps needed in rainfall_data to be considered valid
        time_res:
            Resolution of data (i.e. hourly or 15 min denoted: '1h' or '15m')
        smallest_rainfall_amount:
            Smallest measurable rainfall amount
        min_n_neighbours:
            Minimum number of nearby rain gauges allowed for neighbourhood QC checks.
        qc_framework:
            QC framework to run (see rainfallqc.qc_frameworks/inbuilt_qc_frameworks for options or build your own by looking at RainfallQC docs)
        nearby_rainfall_data_loader_kwargs:
            Any additional arguments to override the defaults of the nearby data loader i.e. distance_threshold and  n_closest (default is {})
        verbose:
            Whether to print progress as algorithm is run (default: False)
        """
        self.station_id_col = station_id_col
        self.station_name_col = station_name_col
        self.date_time_col = date_time_col
        self.precipitation_col = precipitation_col
        self.easting_col = easting_col
        self.northing_col = northing_col
        self.start_date_col = start_date_col
        self.end_date_col = end_date_col
        self.input_crs = self._validate_input_crs(input_crs)
        self.min_n_timesteps = min_n_timesteps
        self.time_res = self._validate_time_res(time_res)
        self.smallest_rainfall_amount = smallest_rainfall_amount
        self.min_n_neighbours = min_n_neighbours
        self.qc_framework = qc_framework
        self.nearby_rainfall_data_loader_kwargs = nearby_rainfall_data_loader_kwargs
        self.output_dir = output_dir
        self.verbose = verbose

        if self.qc_framework == "intenseqc_rulebase_only":
            self.qc_kwargs, self.qc_methods_to_run = self._set_up_intenseqc_framework()

        else:
            raise ValueError(
                f"QC framework: '{self.qc_framework}' not recognised, please select from: 'intenseqc_rulebase_only'"
            )

        if "latitude" not in rainfall_metadata.columns or "longitude" not in rainfall_metadata.columns:
            self.rainfall_metadata = self._add_latlon_to_rainfall_metadata(rainfall_metadata)
        else:
            self.rainfall_metadata = rainfall_metadata
        self.rainfall_data = rainfall_data

    def _add_latlon_to_rainfall_metaddata(self, rainfall_metadata: pl.DataFrame) -> pl.DataFrame:
        return spatial_utils.crs_to_crs(
            rainfall_metadata,
            crs_in=self.input_crs,
            crs_out="EPSG:4326",
            east_west_col_in=self.easting_col,
            north_south_col_in=self.northing_col,
            east_west_col_out="latitude",
            north_south_col_out="longitude",
        )

    def _set_up_intenseqc_framework(self) -> tuple[dict, list]:
        qc_kwargs = {
            "QC2": {"k": 10},
            "shared": {
                "time_res": self.time_res,
                "smallest_measurable_rainfall_amount": self.smallest_rainfall_amount,
                "wet_threshold": 1.0,
                "min_n_neighbours": self.min_n_neighbours,
                "n_neighbours_ignored": 0,
                "accumulation_multiplying_factor": 2.0,
            },
        }

        qc_methods_to_run = ["QC2", "QC10", "QC11", "QC12", "QC13", "QC14", "QC15", "QC17", "QC19", "QC20"]

        return qc_kwargs, qc_methods_to_run

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

    @classmethod
    def run(
        cls, save_data: bool = True, return_data: bool = False, partition_by_columns: list = None, **kwargs
    ) -> None | tuple[pl.DataFrame, pl.DataFrame]:
        """
        Run the quality controller and return and/or save the prepared data.

        Parameters
        ----------
        save_data:
            Whether to save data to output directory (default True)
        return_data:
            Whether to return dataframes (default False)
        partition_by_columns:
            List of columns to partition the parquet files by if saving outputs

        Returns
        -------
        qc_data:
            Data run through algorithm
        qc_metadata:
            Metadata of data run through algorithm

        """
        quality_controller = cls(**kwargs)
        if quality_controller.verbose:
            print("Quality controlling data for gridder")
        quality_controller.quality_control_data()
        if save_data:
            if quality_controller.verbose:
                print(f"Saving data to {quality_controller.output_dir}")
            quality_controller.save_qcd_data(partition_by_columns)
            quality_controller.save_qcd_metadata()
        else:
            if quality_controller.verbose:
                print("Data not saved")
        if return_data:
            return (
                quality_controller.qcd_data,
                quality_controller.qcd_metadata,
                quality_controller.summary_of_qc,
                quality_controller.qc_rulebase_summary,
            )

    def quality_control_data(self):
        # preallocate the list sizes
        unique_station_ids = self.rainfall_metadata[self.station_id_col].unique()
        overall_summary_of_qc = [None] * len(unique_station_ids)
        qcd_data_list = [None] * len(unique_station_ids)
        rulebase_summary = [None] * len(unique_station_ids)

        # begin loop
        for ind, station_id in enumerate(unique_station_ids):
            nearby_gauge_loader = NearbyRainfallDataLoader(
                metadata=self.rainfall_metadata,
                station_id=station_id,
                date_time_col=self.date_time_col,
                precipitation_col=self.precipitation_col,
                station_id_col=self.station_id_col,
                start_datetime_col=self.start_date_col,
                end_datetime_col=self.end_date_col,
                min_overlap_days=self.min_n_timesteps / time_res_to_n_time_steps_in_day[self.time_res],
                rainfall_data_source="df",
                rainfall_data_pl=self.rainfall_data,
                time_res=self.time_res,
                **self.nearby_rainfall_data_loader_kwargs,
            )

            nearby_metadata = nearby_gauge_loader.nearby_metadata
            nearby_rainfall_data = nearby_gauge_loader.load_nearby_gauge_data(rainfall_data=self.rainfall_data)

    def save_qcd_data(self, partition_by_columns: list = None) -> None:
        """
        Save data that has been quality controlled for gridding.

        Parameters
        ----------
        partition_by_columns:
            Columns that decide the partitioning of the output parquet file structure (default is station_id_col)
        """
        if partition_by_columns is None:
            partition_by_columns = [self.station_id_col]

        if self.qcd_data is None:
            raise RuntimeError("You must call quality_control_data() before save_qcd_data()")

        assert len(self.qcd_metadata.filter(pl.col("file_path").is_duplicated())) == 0, (
            "Problem with metadata as duplicate filepaths"
        )

        # Save partitioned parquet file
        (
            self.qcd_data.sort(self.date_time_col).write_parquet(
                self.output_dir / "qc_data",
                partition_by=partition_by_columns,
            )
        )
        if self.verbose:
            print(f"QC'd rainfall data available at: {self.output_dir / 'qc_data/'}")

    def save_qcd_metadata(self) -> None:
        if self.qcd_metadata is None:
            raise RuntimeError("You must call quality_control_data() before save_final_metadata()")
        self.qcd_metadata.write_parquet(self.output_dir / "qcd_metadata.parquet")
        if self.verbose:
            print(f"QC'd rainfall metadata available at: {self.output_dir / 'prepared_metadata.parquet'}")

    def save_summary_of_qc(self) -> None:
        if self.summary_of_qc is None:
            raise RuntimeError("You must call quality_control_data() before summary_of_qc()")
        self.summary_of_qc.write_parquet(self.output_dir / "summary_of_qc.parquet")
        if self.verbose:
            print(f"Summary of QC available at: {self.output_dir / 'summary_of_qc.parquet'}")

    def save_qc_rulebase_summary(self) -> None:
        if self.qc_rulebase_summary is None:
            raise RuntimeError("You must call quality_control_data() before save_qc_rulebase_summary()")
        self.qc_rulebase_summary.write_parquet(self.output_dir / "qc_rulebase_summary.parquet")
        if self.verbose:
            print(f"Summary of QC rulebase available at: {self.output_dir / 'qc_rulebase_summary.parquet'}")