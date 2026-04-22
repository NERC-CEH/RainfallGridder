import xarray as xr


def replace_daily_time_step_hour_with_zero(daily_data: xr.Dataset, date_time_col: str) -> xr.Dataset:
    """
    Replace the hour of the daily dataset with 0.

    Useful if the data has a time step of 12Z instead of 0Z.

    Parameters
    ----------
    daily_data:
        Daily data with date_time_col
    date_time_col:
        Date time column

    Returns
    -------
    daily_data:
        Daily data with date time with hour 0

    """
    replacement_time = daily_data[date_time_col].to_index().map(lambda t: t.replace(hour=0))
    return daily_data.assign_coords(time=replacement_time)
