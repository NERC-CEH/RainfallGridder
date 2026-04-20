import polars as pl
from rainfall_gridder import prepare_data


class DataPreparer:
    def __init__(self, data: pl.DataFrame, metadata: pl.DataFrame, station_id_col: str, date_time_col: str):
        self.data = data
        self.station_id_col = station_id_col
        self.date_time_col = date_time_col
        self.metadata = self._prepare_metadata(metadata)

    def _remove_duplicates_in_metadata(self, metadata):
        return self.metadata.unique(subset=[self.station_id_col])  # TODO: this would leave wrong coords

    def _prepare_metadata(self, metadata):
        metadata = self._remove_duplicates_in_metadata(metadata)
        try:
            prepare_data.metadata_preparer.add_completeness_to_metadata(
                self.data, metadata, station_id_col=self.station_id_col, date_time_col=self.date_time_col
            )
        except ValueError as ve:
            print(ve)

        return prepare_data.metadata_preparer.add_completeness_to_metadata(
            self.data, metadata, station_id_col=self.station_id_col, date_time_col=self.date_time_col
        )

    def prepare(self):
        return self
