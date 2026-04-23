import polars as pl
import xarray as xr


def replace_daily_time_step_hour_with_zero(daily_data: xr.Dataset, time_col: str="time") -> xr.Dataset:
    """
    Replace the hour of the daily dataset with 0.

    Useful if the data has a time step of 12Z instead of 0Z.

    Parameters
    ----------
    daily_data:
        Daily data with date_time_col
    time_col:
        time column (default is 'time')

    Returns
    -------
    daily_data:
        Daily data with date time with hour 0

    """
    replacement_time = daily_data[time_col].to_index().map(lambda t: t.replace(hour=0))
    return daily_data.assign_coords(time=replacement_time)


def subset_gridded_data_to_metadata_bounds(
    gridded_data: xr.Dataset, metadata: pl.DataFrame, easting_col: str, northing_col: str
) -> xr.Dataset:
    """
    Subset xarray data to bounds of metadata (adds a small buffer of size standard deviation).

    Parameters
    ----------
    gridded_data:
        Gridded data to subset
    metadata:
        Metadata with easting and northing column
    easting_col:
        Name of east/west column
    northing_col:
        Name of north/south column

    Returns
    -------
    subset_gridded_data:
        Gridded data subset to easting and northing bounds of metadata
    """
    return gridded_data.sel(
        x=slice(
            metadata[easting_col].min() - metadata[easting_col].std(),
            metadata[easting_col].max() + metadata[easting_col].std(),
        ),
        y=slice(
            metadata[northing_col].min() - metadata[northing_col].std(),
            metadata[northing_col].max() + metadata[northing_col].std(),
        ),
    )
