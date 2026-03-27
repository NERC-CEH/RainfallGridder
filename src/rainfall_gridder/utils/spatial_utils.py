import numpy as np
import xarray as xr

NEAREST_GRID_CELL_TOLERANCE_M = 1000  # metres


def get_nearest_grid_cell(
    data: xr.Dataset,
    easting: int | float,
    northing: int | float,
    tolerance=NEAREST_GRID_CELL_TOLERANCE_M,
) -> xr.Dataset:
    # Should this select the 2*2 grid cells surrounding (in case on edge of a single cell)?
    return data.sel(
        x=easting,
        y=northing,
        method="nearest",
        tolerance=tolerance,
    )


def calculate_gauge_to_grid_centre_distance(x_grid_centre, y_grid_centre, gauge_x, gauge_y):
    """
    Calculate distance between a grid square centre and a gauge
    """
    return np.sqrt((x_grid_centre - gauge_x) ** 2 + (y_grid_centre - gauge_y) ** 2)
