import polars as pl


def set_negative_precip_values_to_none(precip_data: pl.DataFrame, precip_col: str) -> pl.DataFrame:
    """
    Set values below 0 from the precip column to None.

    Parameters
    ----------
    precip_data:
        Data with precipitation column
    precip_col:
        Name of precipitation column

    Returns
    -------
    data_wo_non_neg:
        Data without non-negative precipitation values
    """
    return precip_data.with_columns(
        pl.when(pl.col(precip_col) < 0).then(None).otherwise(pl.col(precip_col)).alias(precip_col)
    )


def group_metadata_by_station_locations(metadata: pl.DataFrame, easting_col: str, northing_col: str) -> pl.DataFrame:
    """
    Group metadata by station locations and give a unique group ID.

    Parameters
    ----------
    metadata:
        Station metadata with easting and northing col
    easting_col:
        Name of easting coord column
    northing_col:
        Name of easting coord column

    Returns
    -------
    metadata_w_groupIDs:
        Metadata with station group ID column
    """
    return metadata.with_columns(pl.struct(easting_col, northing_col).rank(method="dense").alias("station_group_id"))


def add_blank_file_path_to_metadata(metadata: pl.DataFrame) -> pl.DataFrame:
    """
    Add empty file path column to metadata.

    Parameters
    ----------
    metadata:
        Station metadata

    Returns
    -------
    metadata_w_file_paths:
        Metadata with empty file_path column (string)
    """
    return metadata.with_columns(pl.lit(None).cast(pl.String).alias("file_path"))
