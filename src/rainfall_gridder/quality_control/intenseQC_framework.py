from rainfallqc import (
    comparison_checks,
    timeseries_checks,
    gauge_checks,
    neighbourhood_checks,
)

intenseqc_framework = {
    "QC2": {
        "function": gauge_checks.check_years_where_annual_mean_k_top_rows_are_zero,
    },
    "QC10": {
        "function": comparison_checks.check_exceedance_of_rainfall_world_record,
    },
    "QC11": {
        "function": comparison_checks.check_hourly_exceedance_etccdi_rx1day,
    },
    "QC12": {
        "function": timeseries_checks.check_dry_period_cdd,
    },
    "QC13": {
        "function": timeseries_checks.check_daily_accumulations,
    },
    "QC14": {
        "function": timeseries_checks.check_monthly_accumulations,
    },
    "QC15": {
        "function": timeseries_checks.check_streaks,
    },
    "QC17": {
        "function": neighbourhood_checks.check_wet_neighbours,
    },
    "QC19": {
        "function": neighbourhood_checks.check_dry_neighbours,
    },
    "QC20": {
        "function": neighbourhood_checks.check_monthly_neighbours,
    },
}
