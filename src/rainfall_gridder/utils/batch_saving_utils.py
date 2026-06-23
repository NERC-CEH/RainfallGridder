import datetime
import itertools

import polars as pl


def get_all_days_in_input(
    data: pl.DataFrame, start_date_col: str, end_date_col: str, every_n_days: int = 1
) -> list:
    current = data[start_date_col].min()
    end_date = data[end_date_col].max()
    all_days = []
    while current < end_date:
        all_days.append(current)
        current += datetime.timedelta(days=every_n_days)
    return all_days


def batch_days(iterable, n):
    """Yield successive n-sized chunks from iterable."""
    it = iter(iterable)
    while chunk := list(itertools.islice(it, n)):
        yield chunk
