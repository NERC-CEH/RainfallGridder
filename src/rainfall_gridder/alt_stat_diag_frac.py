import numpy as np
import xarray as xr
import datetime
from .stat_disag_fraction import SUMMER_RAINFALL_24H_DISAG, WINTER_RAINFALL_24H_DISAG, interpolate_profile_to_15min


# ── Build lookup array once at module level ──────────────────────────────────
# Bin order matches np.digitize bins below: [<=1, <=5, <=10, <=20, >20]
_BIN_KEYS = [0, 1, 5, 10, 20]  # original dict keys, in bin order


def _build_lookup_array(season_dict: dict) -> np.ndarray:
    """Returns shape (5, 24) array — axes: [bin_idx, hour]"""
    return np.array([season_dict[k] for k in _BIN_KEYS], dtype=np.float64)


def _build_lookup_array_15min(season_dict: dict) -> np.ndarray:
    """Returns shape (5, 96) array — axes: [bin_idx, 15min_step]"""
    hourly = _build_lookup_array(season_dict)  # (5, 24)
    return np.array(
        [interpolate_profile_to_15min(row) for row in hourly], dtype=np.float64
    )  # (5, 96)


# Shape: (2, 5, 24)
DISAG_LOOKUP_1H = np.stack([
    _build_lookup_array(SUMMER_RAINFALL_24H_DISAG),
    _build_lookup_array(WINTER_RAINFALL_24H_DISAG),
], axis=0)

# Shape: (2, 5, 96)
DISAG_LOOKUP_15MIN = np.stack([
    _build_lookup_array_15min(SUMMER_RAINFALL_24H_DISAG),
    _build_lookup_array_15min(WINTER_RAINFALL_24H_DISAG),
], axis=0)

# Bin edges for np.digitize — right=True means: <=1 → 0, <=5 → 1, etc.
_BIN_EDGES = np.array([1, 5, 10, 20])


# ── Vectorised grid function (replaces apply_ufunc) ─────────────────────────
def get_stat_disag_fraction_1h_grid(
    daily_total_grid: xr.DataArray,
    dt: datetime.datetime,
    expected_minute_alignment: int = 0,
) -> xr.DataArray:
    """
    Vectorised version of get_stat_disag_fraction_hourly.
    Operates on the entire 2D grid at once.

    Parameters
    ----------
    daily_total_grid : xr.DataArray
        2D grid of daily precipitation totals (x, y).
    dt : datetime.datetime
        Timestep — provides hour and month.
    expected_minute_alignment : int
        Expected minute value on each timestamp (default 0).
    """
    assert dt.minute == expected_minute_alignment, (
        f"Minute alignment mismatch: got {dt.minute}, expected {expected_minute_alignment}"
    )

    values = daily_total_grid.values  # numpy array, shape (y, x)

    # Season index: 1=winter (Oct-Apr), 0=summer
    month = dt.month
    is_winter = int(month <= 4 or month >= 11)  # scalar

    # Bin index per cell — np.digitize is fully vectorised
    # right=True: bin 0 → val<=1, bin 1 → val<=5, bin 2 → val<=10,
    #             bin 3 → val<=20, bin 4 → val>20
    bin_idx = np.digitize(values, _BIN_EDGES, right=True)  # shape (y, x)

    hour = dt.hour  # scalar

    # Single fancy-index into (2, 5, 24) lookup — no Python loop
    fractions = DISAG_LOOKUP_1H[is_winter, bin_idx, hour]  # shape (y, x)

    # Preserve NaNs from the input
    fractions = np.where(np.isnan(values), np.nan, fractions)

    return xr.DataArray(fractions, coords=daily_total_grid.coords, dims=daily_total_grid.dims)


def get_stat_disag_fraction_15min_grid(
    daily_total_grid: xr.DataArray,
    dt: datetime.datetime,
    expected_minute_alignment: int = 0,
) -> xr.DataArray:
    """
    Vectorised 15-min version of get_stat_disag_fraction_15min.
    Operates on the entire 2D grid at once.
    """
    assert dt.minute % 15 == 0, (
        f"Expected 15-min aligned timestamp, got minute={dt.minute}"
    )

    values = daily_total_grid.values  # (y, x)

    is_winter = int(dt.month <= 4 or dt.month >= 11)
    bin_idx = np.digitize(values, _BIN_EDGES, right=True)  # (y, x)

    # Convert hour + minute to 15-min step index (0–95)
    step_idx = dt.hour * 4 + dt.minute // 15  # scalar, 0–95

    fractions = DISAG_LOOKUP_15MIN[is_winter, bin_idx, step_idx]  # (y, x)
    fractions = np.where(np.isnan(values), np.nan, fractions)

    return xr.DataArray(fractions, coords=daily_total_grid.coords, dims=daily_total_grid.dims)
