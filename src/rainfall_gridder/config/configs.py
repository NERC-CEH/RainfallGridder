from pathlib import Path


def get_ceh_gear_15m_CEH_GEAR_based_kwargs():
    return {
        "gridded_rainfall_col": "rainfall_amount",
        "output_dir": Path("outputs"),
        "rainfall_offset_hours": 10,
        "n_hours": 96,
        "min_n_timesteps": 100,  # TODO: change
    }


def get_ceh_gear_15m_HadUK_Grid_based_kwargs():
    return {
        "gridded_rainfall_col": "rainfall",
        "output_dir": Path("outputs"),
        "rainfall_offset_hours": 9,
        "n_hours": 96,
        "min_n_timesteps": 100,  # TODO: change
    }

