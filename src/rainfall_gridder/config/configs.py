from rainfall_gridder.config.schema import WorkflowConfig, MetadataConfig, DataConfig, ColumnConfig


# Default / local run
DEFAULT_CONFIG = WorkflowConfig(
    metadata=MetadataConfig(path="data/metadata.csv"),
    data=DataConfig(path="data/data.csv"),
)


# Example: alternative column naming
CEH_GEAR_CONFIG = WorkflowConfig(
    metadata=MetadataConfig(
        path="data/metadata_alt.csv",
        columns=ColumnConfig(station_id_col="STN_ID")
    ),
    data=DataConfig(
        path="data/data_alt.csv",
        columns=ColumnConfig(date_time_col="TIMESTAMP")
    ),
)
