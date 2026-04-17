import polars as pl

# NEGATIVE VALUES SET TO NULL
data_w_no_nulls = gauge_data.with_columns(
    pl.when(pl.col(PRECIPITATION_COL) < 0)
    .then(None)
    .otherwise(pl.col(PRECIPITATION_COL))
    .alias(PRECIPITATION_COL)
)


## NOT USED
metadata_only_duplicated = all_metadata.with_columns(pl.len().over(["EASTING", "NORTHING"]).alias("count")).filter(
    pl.col("count") > 1
)


metadata_w_groupIDs = all_metadata.with_columns(
    pl.struct("EASTING", "NORTHING").rank(method="dense").alias("station_group_id")
)


metadata_w_paths = metadata_w_groupIDs.with_columns(pl.lit(None).cast(pl.String).alias("file_path"))
