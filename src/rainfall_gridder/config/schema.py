from pathlib import Path
from pydantic import BaseModel, Field


class ColumnConfig(BaseModel):
    station_id_col: str = "station_id"
    date_time_col: str = "date_time"
    start_date_col: str = "start_date"
    end_date_col: str = "end_date"
    completeness_col: str = "completeness"
    precipitation_col: str = "precipitation"


class MetadataConfig(BaseModel):
    path: Path


class DataConfig(BaseModel):
    path: Path


class WorkflowConfig(BaseModel):
    metadata: MetadataConfig
    data: DataConfig
    output_dir: Path
    rainfall_offset_hours: int
    n_hours: int
    n_months_required: float
    batch_size: int = 5
