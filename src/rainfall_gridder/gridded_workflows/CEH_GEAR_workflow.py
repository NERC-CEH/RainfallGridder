from rainfall_gridder.prepare_data.DataPreparer import DataPreparer
from rainfall_gridder.quality_control import apply_intenseQC_rulebase
from rainfall_gridder.generate_grids import ceh_gear_subdaily_producer

from rainfall_gridder.config.configs import get_ceh_gear_defaults
from rainfall_gridder.config.schema import WorkflowConfig, ColumnConfig

from rainfall_gridder.utils import batch_saving_utils


def ceh_gear_subdaily_workflow(
    data_path: str, metadata_path: str, columns: dict | ColumnConfig | None = None, **overrides
):
    # 1. Build column config (allow overrides)
    if columns is None:
        columns = ColumnConfig()
    elif isinstance(columns, dict):
        columns = ColumnConfig(**columns)

    # 2. Build workflow config (NOTE: match schema structure)
    config = WorkflowConfig(
        **get_ceh_gear_defaults(),
        **overrides,
        data={
            "path": data_path,
        },
        metadata={
            "path": metadata_path,
        },
    )

    # Start workflow
    # 1. Prepare data
    data, metadata = DataPreparer(config.data, config.metadata, columns.date_time_col)

    # 2. Quality Control
    data, metadata = apply_intenseQC_rulebase(data, metadata, config.output_dir)

    # 3. Generate grids
    all_days = batch_saving_utils.get_all_days(
        metadata, start_date_col=config.start_date_col, end_date_col=config.end_date_col
    )

    for batch_days in batch_saving_utils.batch_days(all_days, config.batch_size):
        # batch_results = []
        for time_step in batch_days:
            # one_day_gridded_daily = gridded_daily.sel(time=time_step.replace(minute=0, second=0, microsecond=0)).where(uk_mask) # subset_to_uk_mask to work with map multiplication
            # ceh_gear_sub_daily_producer = CEHGEARSubDailyProducer(rainfall_data, metadata, time_step, data_resolution=TIME_RES,
            #                                                 rain_gauge_col=PRECIPITATION_COL, station_id_col=STATION_ID_COL,
            #                                                 easting_col=EASTING_COL, northing_col=NORTHING_COL, date_col=DATE_TIME_COL,
            #                                                 hour_at_start_of_day=RAINFALL_OFFSET_HOURS)
            # data, metadata = ceh_gear_subdaily_producer(data, metadata, config.output_dir, one_day_gridded)
            pass
        # combined_batch_ds = xr.concat(batch_results, dim=config.datetime_col)
        # batch_saving_utils.write_to_zarr(config.output_zarr_file, zarr_format=2)
        pass

    # 4. Save outputs
    return
