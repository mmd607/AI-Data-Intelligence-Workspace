"""Deterministic statistics for a column classified as datetime.

Re-parses the column with `errors="coerce"` so a value that fails to parse is counted
(`unparseable_count`) rather than silently dropped or crashing the whole profile —
consistent with "Do not fabricate, estimate, or hard-code" (a value we can't parse is
reported as such, not guessed).
"""

import pandas as pd

from app.profiling.schemas import DatetimeColumnStats


def compute_datetime_stats(series: pd.Series) -> DatetimeColumnStats:
    missing_count = int(series.isna().sum())
    non_null = series.dropna()

    parsed = pd.to_datetime(non_null, errors="coerce", format="mixed")
    unparseable_count = int(parsed.isna().sum())
    valid = parsed.dropna()

    if valid.empty:
        min_date = max_date = None
        date_range_days: float | None = None
    else:
        min_date = valid.min().to_pydatetime()
        max_date = valid.max().to_pydatetime()
        date_range_days = (valid.max() - valid.min()).total_seconds() / 86400

    return DatetimeColumnStats(
        min_date=min_date,
        max_date=max_date,
        date_range_days=date_range_days,
        missing_count=missing_count,
        unparseable_count=unparseable_count,
    )
