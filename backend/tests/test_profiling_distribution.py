"""Tests for deterministic histogram/distribution generation."""

import pandas as pd

from app.profiling.distribution import compute_distributions


def test_histogram_bin_counts_sum_to_row_count() -> None:
    df = pd.DataFrame({"value": list(range(100))})
    result = compute_distributions("ds1", df, bin_count=10)

    assert len(result.columns) == 1
    column = result.columns[0]
    assert column.bin_count == 10
    assert sum(b.count for b in column.bins) == 100
    assert column.min == 0
    assert column.max == 99


def test_non_numeric_columns_are_skipped() -> None:
    df = pd.DataFrame({"category": ["a", "b", "c"]})
    result = compute_distributions("ds1", df)
    assert result.columns == []
    assert "category" in result.skipped_columns


def test_boolean_columns_are_skipped() -> None:
    df = pd.DataFrame({"flag": [True, False, True]})
    result = compute_distributions("ds1", df)
    assert "flag" in result.skipped_columns


def test_single_distinct_value_produces_one_bin() -> None:
    df = pd.DataFrame({"value": [7, 7, 7, 7]})
    result = compute_distributions("ds1", df)
    column = result.columns[0]
    assert column.bin_count == 1
    assert column.bins[0].count == 4
    assert column.bins[0].bin_start == 7
    assert column.bins[0].bin_end == 7


def test_all_null_numeric_column_is_skipped() -> None:
    df = pd.DataFrame({"value": [None, None, None]})
    df["value"] = df["value"].astype("float64")
    result = compute_distributions("ds1", df)
    assert "value" in result.skipped_columns
    assert result.columns == []


def test_infinite_values_excluded_but_finite_values_still_binned() -> None:
    df = pd.DataFrame({"ratio": [1.0, 2.0, 3.0, float("inf"), float("-inf")]})
    result = compute_distributions("ds1", df, bin_count=3)
    column = result.columns[0]
    assert sum(b.count for b in column.bins) == 3  # only the 3 finite values
    assert column.min == 1.0
    assert column.max == 3.0


def test_deterministic_repeated_computation() -> None:
    df = pd.DataFrame({"value": [1, 5, 3, 8, 2, 9, 4]})
    first = compute_distributions("ds1", df)
    second = compute_distributions("ds1", df)
    # generated_at legitimately differs between calls (it's a real timestamp) — compare
    # everything else, which must be byte-for-byte identical.
    assert first.model_dump(exclude={"generated_at"}) == second.model_dump(exclude={"generated_at"})
