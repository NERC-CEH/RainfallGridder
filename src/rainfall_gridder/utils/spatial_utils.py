import numpy as np
import polars as pl
import xarray as xr
from pyproj import Transformer

NEAREST_GRID_CELL_TOLERANCE_M = 1000  # metres


def calculate_gauge_to_grid_centre_distance(x_grid_centre, y_grid_centre, gauge_x, gauge_y):
    """
    Calculate distance between a grid square centre and a gauge
    """
    return np.sqrt((x_grid_centre - gauge_x) ** 2 + (y_grid_centre - gauge_y) ** 2)


def crs_to_crs(
    df: pl.DataFrame,
    crs_in: int | str,
    crs_out: int | str,
    east_west_col_in: str,
    north_south_col_in: str,
    east_west_col_out: str,
    north_south_col_out: str,
) -> pl.DataFrame:
    """
    Convert a dataframe from one crs into another

    Parameters
    ##########
    df:
        Data to be converted with east and north coordinates
    crs_in:
        Coordinate reference system from
    crs_out:
        Coordinate reference system to
    east_west_col_in:
        Input east/west coordinate column (e.g. longitude)
    north_south_col_in:
        Input north/south coordinate column (e.g. latitude)
    east_west_col_out:
        Output east/west coordinate column (e.g. Easting)
    north_south_col_out:
        Output north/south coordinate column (e.g. South)

    Returns
    #######
    df: dataframe
        Data with new crs
    """
    if not crs_in.startswith("EPSG"):
        crs_in = "EPSG:" + str(crs_in)
    if not crs_out.startswith("EPSG"):
        crs_out = "EPSG:" + str(crs_out)
    transformer = Transformer.from_crs(crs_in, crs_out, always_xy=True)
    transformed_eastings, transformed_northings  = transformer.transform(
        df[east_west_col_in].to_numpy(), df[north_south_col_in].to_numpy()
    )
    return df.with_columns(pl.lit(transformed_eastings).alias(east_west_col_out),
                    pl.lit(transformed_northings).alias(north_south_col_out))


def get_nearest_grid_cell(
    data: xr.Dataset,
    easting: int | float,
    northing: int | float,
    tolerance: int = NEAREST_GRID_CELL_TOLERANCE_M,
) -> xr.Dataset:
    # Should this select the 2*2 grid cells surrounding (in case on edge of a single cell)?
    return data.sel(
        x=easting,
        y=northing,
        method="nearest",
        tolerance=tolerance,
    )
