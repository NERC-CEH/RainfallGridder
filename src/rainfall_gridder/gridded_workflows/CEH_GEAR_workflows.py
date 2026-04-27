from pathlib import Path
import polars as pl
import xarray as xr
from rainfall_gridder.config.schema import ColumnConfig, WorkflowConfig
from rainfall_gridder.prepare_data.DataPreparer import DataPreparer
from rainfall_gridder.quality_control.QualityController import QualityController
from rainfall_gridder.prepare_data.gauge_grid_correlator import BatchGaugeVsGriddedCorrelator
from rainfall_gridder.generate_grids.ceh_gear_subdaily_producer import CEHGEARSubDailyProducer
from rainfall_gridder.utils import batch_saving_utils, get_ceh_gear_data, spatial_utils


def ceh_gear_subdaily_workflow(
    rainfall_data_path: str | Path,
    rainfall_metadata_path: str | Path,
    gridded_rainfall_path: str | Path | xr.Dataset,
    default_ceh_gear_kwargs: dict,
    gridded_rainfall_rename_dict: dict | None = None,
    data_columns: dict | ColumnConfig | None = None,
    **overrides,
) -> None:
    """
    Workflow for preparing, quality controlling and gridding rain gauge data onto CEH-GEAR subdaily product.

    Parameters
    ----------
    rainfall_data_path:
       Path to rain gauge data
    rainfall_metadata_path:
        Path to metadata for the rain gauge data
    gridded_rainfall_path:
        Path to gridded rainfall data (e.g. HadUK-Grid)
    default_ceh_gear_kwargs:
        Default arguments for CEH-GEAR workflow (see config/configs.py)
    gridded_rainfall_rename_dict:
        Columns to rename
    data_columns:
        Names of the columns in rainfall data and metadata (will default to standard names, see config/schema.py)
    overrides:
        Any arguments to override in the defaults of CEH-GEAR workflow or Workflowconfig

    """
    # 1. Build column config (allow overrides)
    if data_columns is None:
        data_columns = ColumnConfig()
    elif isinstance(data_columns, dict):
        data_columns = ColumnConfig(**data_columns)

    # 2. Build workflow config (NOTE: match schema structure)
    config = WorkflowConfig(
        **default_ceh_gear_kwargs,
        **overrides,  # will silent win against default ceh_gear_kwargs
        rainfall_data={
            "path": rainfall_data_path,
        },
        rainfall_metadata={
            "path": rainfall_metadata_path,
        },
        gridded_rainfall_data={
            "path": gridded_rainfall_path,
            "rename": gridded_rainfall_rename_dict or {},
        },
        data_columns=data_columns,
    )
    # 0. Load in data
    print("0. Load in data")
    rainfall_data = config.load_rainfall_data()
    rainfall_metadata = config.load_rainfall_metadata()
    gridded_rainfall = config.load_gridded_rainfall()

    # Start workflow
    # 1. Prepare data
    print("1. Prepare data")
    rainfall_data, rainfall_metadata = DataPreparer.run(
        rainfall_data=rainfall_data,
        rainfall_metadata=rainfall_metadata,
        station_id_col=config.data_columns.station_id_col,
        station_name_col=config.data_columns.station_name_col,
        precipitation_col=config.data_columns.precipitation_col,
        date_time_col=config.data_columns.date_time_col,
        start_date_col=config.data_columns.start_date_col,
        end_date_col=config.data_columns.end_date_col,
        easting_col=config.data_columns.easting_col,
        northing_col=config.data_columns.northing_col,
        gridded_rainfall_data=gridded_rainfall,
        gridded_rainfall_col=config.gridded_rainfall_col,
        rainfall_offset_hours=config.rainfall_offset_hours,
        output_dir=config.output_dir,
        verbose=config.verbose,
        min_n_timesteps=config.min_n_timesteps,
        save_data=True,
        return_data=True,
    )

    # 2. Quality Control
    print("2. Quality control")
    qcd_rainfall_data, qcd_rainfall_metadata, summary_of_qc, qc_rulebase_summary = QualityController.run(
        rainfall_data=rainfall_data,
        rainfall_metadata=rainfall_metadata,
        station_id_col=config.data_columns.station_id_col,
        station_name_col=config.data_columns.station_name_col,
        date_time_col=config.data_columns.date_time_col,
        precipitation_col=config.data_columns.precipitation_col,
        easting_col=config.data_columns.easting_col,
        northing_col=config.data_columns.northing_col,
        start_date_col=config.data_columns.start_date_col,
        end_date_col=config.data_columns.end_date_col,
        input_crs=config.input_crs,
        output_dir=config.output_dir,
        min_n_timesteps=config.min_n_timesteps,
        time_res=config.time_res,
        smallest_rainfall_amount=config.smallest_rainfall_amount,
        min_n_neighbours=config.min_n_neighbours,
        verbose=config.verbose,
        qc_framework=config.qc_framework,
        nearby_rainfall_data_loader_kwargs=config.nearby_rainfall_data_loader_kwargs,
        save_data=True,
        return_data=True,
    )
    # 3. Correlate gauge and gridded data (agg. to daily)
    print("3. Correlate gauge data to gridded data")
    station_ids_to_correlate = qcd_rainfall_metadata[config.data_columns.station_id_col].unique()
    corrd_rainfall_metadata = BatchGaugeVsGriddedCorrelator.run(
        gauge_data=qcd_rainfall_data,
        gauge_metadata=qcd_rainfall_metadata,
        gridded_rainfall_data=gridded_rainfall,
        gridded_rainfall_col=config.gridded_rainfall_col,
        station_ids_to_correlate=station_ids_to_correlate,
        station_id_col=config.data_columns.station_id_col,
        precipitation_col=config.data_columns.precipitation_col,
        date_time_col=config.data_columns.date_time_col,
        start_date_col=config.data_columns.start_date_col,
        end_date_col=config.data_columns.end_date_col,
        easting_col=config.data_columns.easting_col,
        northing_col=config.data_columns.northing_col,
        rainfall_offset_hours=config.rainfall_offset_hours,
        verbose=config.verbose,
        correlation_threshold=config.correlation_threshold,
        output_dir=config.output_dir,
        save_metadata=True,
        return_metadata=True,
    )

    # 4. Generate grids
    print("4. Generate grids")
    all_days = batch_saving_utils.get_all_days(
        corrd_rainfall_metadata, start_date_col=config.start_date_col, end_date_col=config.end_date_col
    )
    output_grid = get_ceh_gear_data.get_uk_mask_haduk_coords()

    # Subset/clip output grid and gridded daily to metadata bounds
    gridded_rainfall, output_grid = clip_rainfall_grids_to_metadata_bounds(gridded_rainfall, output_grid, config, corrd_rainfall_metadata)

    # corrd_rainfall_metadata[]
    for batch_days in batch_saving_utils.batch_days(all_days, config.batch_size):
        batch_results = []
        for time_step in batch_days:
            one_day_gridded_daily = gridded_rainfall.sel(
                time=time_step.replace(minute=0, second=0, microsecond=0)
            ).where(output_grid)  # subset_to_uk_mask to work with map multiplication

            ceh_gear_sub_daily_producer = CEHGEARSubDailyProducer(
                qcd_rainfall_data,
                corrd_rainfall_metadata,
                time_step,
                data_resolution=TIME_RES,
                precipitation_col=config.data_columns.precipitation_col,
                station_id_col=STATION_ID_COL,
                easting_col=EASTING_COL,
                northing_col=NORTHING_COL,
                date_col=DATE_TIME_COL,
                hour_at_start_of_day=RAINFALL_OFFSET_HOURS,
            )
            # data, metadata = ceh_gear_subdaily_producer(data, metadata, config.output_dir, one_day_gridded)
            pass
        combined_batch_ds = xr.concat(batch_results, dim=config.datetime_col)
        batch_saving_utils.write_to_zarr(
            config.output_dir / config.output_zarr_name, zarr_format=2
        )  # Check if Zarr 3 can be used

def clip_rainfall_grids_to_metadata_bounds(gridded_rainfall: xr.Dataset, output_grid: xr.Dataset, config: WorkflowConfig, metadata: pl.DataFrame) -> tuple[xr.Dataset, xr.Dataset]:

    gridded_rainfall = spatial_utils.clip_grid_to_bounds_with_buffer(
        gridded_rainfall,
        min_easting=metadata[config.data_columns.easting_col].min(),
        max_easting=metadata[config.data_columns.easting_col].max(),
        easting_buffer=metadata[config.data_columns.easting_col].std(),
        min_northing=metadata[config.data_columns.northing_col].min(),
        max_northing=metadata[config.data_columns.northing_col].max(),
        northing_buffer=metadata[config.data_columns.northing_col].std(),
    )

    output_grid = spatial_utils.clip_grid_to_bounds_with_buffer(
        output_grid,
        min_easting=metadata[config.data_columns.easting_col].min(),
        max_easting=metadata[config.data_columns.easting_col].max(),
        easting_buffer=metadata[config.data_columns.easting_col].std(),
        min_northing=metadata[config.data_columns.northing_col].min(),
        max_northing=metadata[config.data_columns.northing_col].max(),
        northing_buffer=metadata[config.data_columns.northing_col].std(),
    )
    return gridded_rainfall, output_grid


    # 4. Save outputs
