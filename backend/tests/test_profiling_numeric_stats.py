"""Golden-value tests for numeric statistics against hand-computed expected values."""

import pandas as pd

from app.profiling.numeric_stats import _safe_float, compute_numeric_stats


class TestSafeFloat:
    """`_safe_float` is a small, exported-in-spirit defensive utility: guarantee a NaN
    never leaks into the API as an invalid JSON token. No current caller happens to pass
    it a NaN (every call site is already guarded), but the contract itself is real and
    worth verifying directly rather than only through the call sites that avoid it.
    """

    def test_nan_becomes_none(self) -> None:
        assert _safe_float(float("nan")) is None

    def test_none_stays_none(self) -> None:
        assert _safe_float(None) is None

    def test_ordinary_value_passes_through(self) -> None:
        assert _safe_float(3.5) == 3.5


def test_stats_for_one_through_ten() -> None:
    series = pd.Series(range(1, 11), name="value")  # 1..10
    stats = compute_numeric_stats(series)

    assert stats.min == 1
    assert stats.max == 10
    assert stats.mean == 5.5
    assert stats.median == 5.5
    assert stats.q1 == 3.25
    assert stats.q3 == 7.75
    assert stats.iqr == 4.5
    assert stats.zero_count == 0
    assert stats.negative_count == 0
    assert stats.infinite_count == 0
    assert abs(stats.std - 3.0276503540974917) < 1e-9


def test_zero_and_negative_counts() -> None:
    series = pd.Series([-5, -3, 0, 0, 2, 4], name="score")
    stats = compute_numeric_stats(series)
    assert stats.zero_count == 2
    assert stats.negative_count == 2


def test_infinite_values_excluded_from_descriptive_stats_but_counted() -> None:
    series = pd.Series([1.0, 2.0, float("inf"), float("-inf"), 3.0], name="ratio")
    stats = compute_numeric_stats(series)
    assert stats.infinite_count == 2
    # Descriptive stats computed only over the finite subset [1.0, 2.0, 3.0].
    assert stats.min == 1.0
    assert stats.max == 3.0
    assert stats.mean == 2.0
    assert stats.negative_count == 1  # -inf still counts as negative


def test_all_null_column_returns_none_stats_not_nan_or_crash() -> None:
    series = pd.Series([None, None, None], name="empty", dtype="float64")
    stats = compute_numeric_stats(series)
    assert stats.min is None
    assert stats.max is None
    assert stats.mean is None
    assert stats.std is None
    assert stats.zero_count == 0
    assert stats.infinite_count == 0


def test_single_value_has_no_std_but_has_min_max_mean() -> None:
    series = pd.Series([42], name="single")
    stats = compute_numeric_stats(series)
    assert stats.min == 42
    assert stats.max == 42
    assert stats.mean == 42
    assert stats.std is None


def test_deterministic_repeated_computation() -> None:
    series = pd.Series([3, 1, 4, 1, 5, 9, 2, 6])
    first = compute_numeric_stats(series)
    second = compute_numeric_stats(series)
    assert first == second
