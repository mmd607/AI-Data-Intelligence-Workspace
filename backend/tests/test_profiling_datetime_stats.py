"""Golden-value tests for datetime statistics."""

import pandas as pd

from app.profiling.datetime_stats import compute_datetime_stats


def test_min_max_and_range_for_known_dates() -> None:
    series = pd.Series(["2024-01-01", "2024-01-10", "2024-02-01"], name="signup_date")
    stats = compute_datetime_stats(series)

    assert stats.min_date.year == 2024
    assert stats.min_date.month == 1
    assert stats.min_date.day == 1
    assert stats.max_date.month == 2
    assert stats.max_date.day == 1
    assert stats.date_range_days == 31.0
    assert stats.missing_count == 0
    assert stats.unparseable_count == 0


def test_missing_values_counted_separately_from_unparseable() -> None:
    series = pd.Series(["2024-01-01", None, "not a date", "2024-02-01"], name="signup_date")
    stats = compute_datetime_stats(series)
    assert stats.missing_count == 1
    assert stats.unparseable_count == 1  # "not a date" — present but unparseable


def test_all_unparseable_returns_none_range_not_crash() -> None:
    series = pd.Series(["junk", "also junk"], name="signup_date")
    stats = compute_datetime_stats(series)
    assert stats.min_date is None
    assert stats.max_date is None
    assert stats.date_range_days is None
    assert stats.unparseable_count == 2


def test_single_date_has_zero_range() -> None:
    series = pd.Series(["2024-01-01"], name="signup_date")
    stats = compute_datetime_stats(series)
    assert stats.date_range_days == 0.0
