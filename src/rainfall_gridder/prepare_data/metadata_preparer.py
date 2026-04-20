import polars as pl


def add_start_and_end_dates_to_metadata(
    data: pl.DataFrame, metadata: pl.DataFrame, station_id_col: str, date_time_col: str
) -> pl.DataFrame:
    """
    Add start and end dates to a dataframe

    Parameters
    ----------
    data :
        Timeseries data with ID and date_time columns
    metadata :
        Metadata with ID column
    station_id_col :
        Column with ID
    date_time_col :
        Column with date_time info

    Returns
    -------
    metadata :
        Metadata with start and end date columns added
    """

    # Add start and end dates to metadata, not necessary if you remove duplicates
    return metadata.join(
        data.group_by(station_id_col).agg(
            pl.col(date_time_col).min().alias("start_date"), pl.col(date_time_col).max().alias("end_date")
        ),
        on=station_id_col,
    )


def add_completeness_to_metadata(
    data: pl.DataFrame, metadata: pl.DataFrame, station_id_col: str, date_time_col: str
) -> pl.DataFrame:
    """
    Add completeness to a dataframe

    Parameters
    ----------
    data :
        Timeseries data with ID and date_time columns
    metadata :
        Metadata with ID column
    station_id_col :
        Column with ID
    date_time_col :
        Column with date_time info

    Returns
    -------
    metadata :
        Metadata with completeness column

    """
    # 1. Check if there are duplicates in the station IDs.
    check_duplicates_in_metadata(metadata, cols_to_check=station_id_col)

    metadata = add_start_and_end_dates_to_metadata(
        data, metadata, station_id_col=station_id_col, date_time_col=date_time_col
    )

    # Aggregate start, end, and actual count per station
    completeness_summary = data.group_by(station_id_col).agg(
        [
            pl.col(date_time_col).min().alias("start_date"),
            pl.col(date_time_col).max().alias("end_date"),
            pl.count(date_time_col).alias("time_steps"),
        ]
    )

    # Compute expected steps and completeness using total_minutes()
    completeness_summary = completeness_summary.with_columns(
        [
            ((pl.col("end_date") - pl.col("start_date")).dt.total_minutes() / 15 + 1).alias("time_steps"),
            (
                (
                    pl.col("time_steps")
                    / ((pl.col("end_date") - pl.col("start_date")).dt.total_minutes() / 15 + 1)
                    * 100
                ).round(1)
            ).alias("completeness"),
        ]
    )

    return metadata.join(completeness_summary[[station_id_col, "completeness"]], on=station_id_col)


def check_col_content_is_identical(metadata: pl.DataFrame, col: str):
    assert len(metadata[col].unique()) == 1, f"Not all values in {col} are identical: '{metadata[col].unique()}'"


def combine_metadata_col_contents(metadata: pl.DataFrame, col: str) -> str:
    return "-".join(str(row_val) for row_val in sorted(metadata[col].unique().to_list()))


def check_duplicates_in_metadata(metadata: pl.DataFrame, cols_to_check: str | list):
    if isinstance(cols_to_check, str):
        cols_to_check = [cols_to_check]
    for col in cols_to_check:
        duplicated_cols = metadata.filter(pl.col(col).is_duplicated())
        if duplicated_cols.height > 0:
            raise ValueError(
                f"Cannot continue as the metadata contains duplicates for the column: '{col}' and values: `{duplicated_cols[col].unique().to_list()}`. Please check those rows and remove or rename them."
            )


class MetadataMerger:
    def __init__(
        self,
        metadata: pl.DataFrame,
        cols_to_check_identical: list,
        cols_to_combine: list,
        start_date_col: str,
        end_date_col: str,
    ):
        self.metadata = metadata
        self.cols_to_combine = cols_to_combine
        self.cols_to_check_identical = cols_to_check_identical
        self.start_date_col = start_date_col
        self.end_date_col = end_date_col
        self._check_for_identical_values_in_col()

    def _check_for_identical_values_in_col(self):
        for col in self.cols_to_check_identical:
            check_col_content_is_identical(self.metadata, col)

    def merge_group_metadata(self, group_name, group_name_col, min_datetime, max_datetime, completeness_col):
        combined_data = {}
        combined_data[group_name_col] = group_name
        for col in self.cols_to_combine:
            combined_data[col] = combine_metadata_col_contents(self.metadata, col)
        for col in self.cols_to_check_identical:
            combined_data[col] = self.metadata[col][0]

        combined_data[self.start_date_col] = min_datetime
        combined_data[self.end_date_col] = max_datetime
        combined_data[completeness_col] = None  # Temporary workaround

        # Fill in missing columns with None
        for col in self.metadata.columns:
            if col not in combined_data.keys():
                try:
                    check_col_content_is_identical(self.metadata, col)
                    combined_data[col] = self.metadata[col][0]
                except AssertionError:
                    combined_data[col] = None

        return pl.DataFrame(combined_data)
