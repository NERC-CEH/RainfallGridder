from rainfall_gridder.prepare_data.DataPreparer import DataPreparer
from rainfall_gridder.quality_control import apply_intenseQC_rulebase 
from rainfall_gridder.generate_grids import ceh_gear_subdaily_producer

from rainfall_gridder.config.configs import get_ceh_gear_defaults
from rainfall_gridder.config.schema import WorkflowConfig, ColumnConfig


def ceh_gear_subdaily_workflow(
    data_path: str,
    metadata_path: str,
    columns: dict | ColumnConfig | None = None,
    **overrides
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
    data, metadata = ceh_gear_subdaily_producer(data, metadata, config.output_dir)
    
    # 4. Save outputs
    return