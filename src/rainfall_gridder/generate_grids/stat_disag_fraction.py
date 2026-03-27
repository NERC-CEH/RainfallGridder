import datetime
import numpy as np

# These are the design storms for different daily totals and seasons. Summer MJJASO is defined as Winter is NDJFMA.
SUMMER_RAINFALL_24H_DISAG = {
    20: [
        0,
        0.075045363,
        0.111588896,
        0.109285183,
        0.106922183,
        0.101722561,
        0.095522696,
        0.086937686,
        0.077334257,
        0.06504227,
        0.053631318,
        0.043644983,
        0.033842388,
        0.023942204,
        0.015538012,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ],
    10: [
        0,
        0.133174186,
        0.187610844,
        0.17096396,
        0.149387402,
        0.12261396,
        0.095364832,
        0.071772478,
        0.048136004,
        0.020976333,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ],
    5: [
        0,
        0.224489575,
        0.268294215,
        0.204391226,
        0.144327357,
        0.096306382,
        0.052866018,
        0.009325227,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ],
    1: [
        0,
        0.454465932,
        0.343457282,
        0.167346649,
        0.034730137,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ],
    0: [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
}

WINTER_RAINFALL_24H_DISAG = {
    20: [
        0,
        0.038522817,
        0.065195361,
        0.078507131,
        0.085227562,
        0.088830993,
        0.08765551,
        0.083918247,
        0.077344225,
        0.069961625,
        0.062781144,
        0.056141098,
        0.049685508,
        0.043508304,
        0.036612424,
        0.029751426,
        0.022080655,
        0.014818826,
        0.009457142,
        0,
        0,
        0,
        0,
        0,
    ],
    10: [
        0,
        0.0728856,
        0.13370783,
        0.151491388,
        0.149074227,
        0.133697489,
        0.111151423,
        0.087111001,
        0.065900303,
        0.049480495,
        0.032250544,
        0.013249701,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ],
    5: [
        0,
        0.14399742,
        0.225675622,
        0.209658632,
        0.165713793,
        0.119380747,
        0.079924,
        0.046307486,
        0.009342299,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ],
    1: [
        0,
        0.370337798,
        0.339630409,
        0.19501892,
        0.095012873,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ],
    0: [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
}


def get_stat_disag_fraction_hourly(daily_total: float, dt: datetime.datetime, expected_minute_allignment: int = 0):
    """
    Apply the design storm disaggregation fraction.

    Parameters
    ----------
    daily_total :
        Daily precipitation total
    dt :
        Datetime containing hour and day-of-year information
    expected_minute_allignment :
        The expected allignment of the minute in each time stamp (default is :00).
    """
    if np.isnan(daily_total):
        return np.nan

    # Winter defined as Oct 31 – Apr 30 (LIKE OG METHOD)
    month = dt.month
    hour = dt.hour
    minute = dt.minute
    assert minute == expected_minute_allignment, (
        f"allignment of data not in expected format for 1 hourly min e.g. :00. Currently: {minute}, expected is: {expected_minute_allignment}. Consider changing expected_minute_allignment if this is expected"
    )

    is_winter = month <= 4 or month >= 11

    season_dict = WINTER_RAINFALL_24H_DISAG if is_winter else SUMMER_RAINFALL_24H_DISAG

    # Determine daily total bin
    if daily_total <= 1:
        bin_key = 0
    elif daily_total <= 5:
        bin_key = 1
    elif daily_total <= 10:
        bin_key = 5
    elif daily_total <= 20:
        bin_key = 10
    else:
        bin_key = 20
    return season_dict[bin_key][hour]


def get_stat_disag_fraction_15min(
    daily_total: float, dt: datetime.datetime, expected_minute_allignments: tuple = (0, 15, 30, 45)
):
    """
    Apply the design storm disaggregation fraction at 15mins.

    Parameters
    ----------
    daily_total :
        Daily precipitation total
    dt :
        Datetime containing minute, hour and day-of-year information
    expected_minute_allignment :
        The expected allignment of the minutes in each time stamp (default is :00, :15, :30, :45).
    """
    if np.isnan(daily_total):
        return np.nan

    # Winter defined as Oct 31 – Apr 30 (LIKE OG METHOD)
    month = dt.month
    hour = dt.hour
    minute = dt.minute
    assert minute in expected_minute_allignments, (
        f"allignment of data not in expected format for 15 min e.g. :00, :15, :30, :45. Currently: {dt}, expected is: {expected_minute_allignments}. Consider changing expected_minute_allignments if this is expected"
    )
    is_winter = month <= 4 or month >= 11

    season_dict = WINTER_RAINFALL_24H_DISAG if is_winter else SUMMER_RAINFALL_24H_DISAG

    # Determine daily total bin
    if daily_total <= 1:
        bin_key = 0
    elif daily_total <= 5:
        bin_key = 1
    elif daily_total <= 10:
        bin_key = 5
    elif daily_total <= 20:
        bin_key = 10
    else:
        bin_key = 20

    season_dict_15min = interpolate_profile_to_15min(season_dict[bin_key])
    # Get segment of hour returns 0, 1, 2, 3 for :00, :15, :30, :45
    segment = minute // 15  # TODO: test with different resolutions
    return season_dict_15min[hour * 4 + segment]


def interpolate_profile_to_15min(profile_24):
    """
    Interpolate a 24-hour rainfall profile to 96 (15-min) values.

    Parameters
    ----------
    profile_24 : list[float]
        24 hourly rainfall fractions.

    Returns
    -------
    list[float]
        96 interpolated 15-minute fractions.
    """

    if len(profile_24) != 24:
        raise ValueError("Profile must have 24 values")

    profile_24 = np.asarray(profile_24, dtype=float)

    # original hourly positions
    x_hour = np.arange(24)

    # 15-minute positions
    x_15min = np.arange(0, 24, 0.25)  # 96 points

    profile_96 = np.interp(x_15min, x_hour, profile_24)

    # renormalise to preserve rainfall mass
    profile_96 *= profile_24.sum() / profile_96.sum()

    return profile_96.tolist()
