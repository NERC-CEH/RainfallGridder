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

    metadata = add_start_and_end_dates_to_metadata(
        data, metadata, station_id_col=station_id_col, date_time_col=date_time_col
    )

    # Aggregate start, end, and actual count per station
    completeness_summary = data.group_by(station_id_col).agg(
        [pl.col("start_date"), pl.col("end_date"), pl.count(date_time_col).alias("time_steps")]
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
