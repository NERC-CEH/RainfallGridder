import polars as pl

from rainfallqc.utils.data_utils import check_data_has_consistent_time_step


def check_data_is_specific_time_res(data: pl.DataFrame, time_res: str | list) -> None:
    """
    Check data has a hourly or daily time step.

    Taken from RainfallQC.
    
    Does not work for monthly data, please use 'check_data_is_monthly'.

    Parameters
    ----------
    data :
        Data with time column.
    time_res :
        Time resolutions either a single string or list of strings

    Raises
    ------
    ValueError :
        If data is not hourly or daily.

    """
    return check_data_has_consistent_time_step(data, time_res)