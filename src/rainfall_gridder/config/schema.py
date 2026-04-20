from dataclasses import dataclass, field

# STATION_ID_COL = "station_id"
# DATE_TIME_COL = "date_time"
# START_DATE_COL = "start_date"
# END_DATE_COL = "end_date"
# COMPETENESS_COL = "completeness"
# PRECIPITATION_COL = "precipitation"
# RAINFALL_OFFSET_HOURS = 10 # GEAR
# N_HOURS = 96 # 96 for 15 mins
# N_MONTHS_REQUIRED = 0.5 # for testing
# OUTPUT_DIR = Path("outputs")
# PARTITION_BY_COLUMNS = [STATION_ID_COL]


@dataclass
class ColumnConfig:
    station_id_col: str = "station_id"
    date_time_col: str = "date_time"
    start_date_col: str = "start_date"
    end_date_col: str = "end_date"
    completeness_col: str = "completeness"
    precipitation_col: str = "precipitation"


@dataclass
class MetadataConfig:
    path: str
    columns: ColumnConfig = field(default_factory=ColumnConfig)


@dataclass
class DataConfig:
    path: str
    columns: ColumnConfig = field(default_factory=ColumnConfig)


@dataclass
class WorkflowConfig:
    metadata: MetadataConfig
    data: DataConfig