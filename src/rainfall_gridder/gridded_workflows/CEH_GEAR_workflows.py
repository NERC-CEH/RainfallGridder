from pathlib import Path
import xarray as xr
from rainfall_gridder.config.schema import ColumnConfig, WorkflowConfig
from rainfall_gridder.prepare_data.DataPreparer import DataPreparer


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
    data = config.load_rainfall_data()
    metadata = config.load_rainfall_metadata()
    gridded_rainfall = config.load_gridded_rainfall()

    # Start workflow
    # 1. Prepare data
    print("1. Prepare data")
    data, metadata = DataPreparer.run(
        data=data,
        metadata=metadata,
        station_id_col=config.data_columns.station_id_col,
        station_name_col=config.data_columns.station_name_col,
        precipitation_col=config.data_columns.precipitation_col,
        date_time_col=config.data_columns.date_time_col,
        start_date_col=config.data_columns.start_date_col,
        end_date_col=config.data_columns.end_date_col,
        easting_col=config.data_columns.easting_col,
        northing_col=config.data_columns.northing_col,
        gridded_rainfall_data=gridded_rainfall,
        gridded_rainfall_col=config.rainfall_col,
        rainfall_offset_hours=config.rainfall_offset_hours,
        output_dir=config.output_dir,
        verbose=config.verbose,
        min_n_timesteps=config.min_n_timesteps,
        save_data=True,
        return_data=True,
    )

    # 2. Quality Control
    print("2. Quality control")
    # data, metadata = apply_intenseQC_rulebase(data, metadata, config.output_dir)

    # 3. Generate grids
    print("3. Generate grids")
    # all_days = batch_saving_utils.get_all_days(
    #     metadata, start_date_col=config.start_date_col, end_date_col=config.end_date_col
    # )

    # for batch_days in batch_saving_utils.batch_days(all_days, config.batch_size):
    #     # batch_results = []
    #     for time_step in batch_days:
    #         # one_day_gridded_daily = gridded_daily.sel(time=time_step.replace(minute=0, second=0, microsecond=0)).where(uk_mask) # subset_to_uk_mask to work with map multiplication
    #         # ceh_gear_sub_daily_producer = CEHGEARSubDailyProducer(rainfall_data, metadata, time_step, data_resolution=TIME_RES,
    #         #                                                 rain_gauge_col=PRECIPITATION_COL, station_id_col=STATION_ID_COL,
    #         #                                                 easting_col=EASTING_COL, northing_col=NORTHING_COL, date_col=DATE_TIME_COL,
    #         #                                                 hour_at_start_of_day=RAINFALL_OFFSET_HOURS)
    #         # data, metadata = ceh_gear_subdaily_producer(data, metadata, config.output_dir, one_day_gridded)
    #         pass
    #     # combined_batch_ds = xr.concat(batch_results, dim=config.datetime_col)
    #     # batch_saving_utils.write_to_zarr(config.output_zarr_file, zarr_format=2)
    #     pass

    # 4. Save outputs
    return
