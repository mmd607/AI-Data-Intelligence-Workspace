"""Golden-value tests for categorical statistics."""

import pandas as pd

from app.profiling.categorical_stats import compute_categorical_stats


def test_top_values_and_cardinality() -> None:
    series = pd.Series(["A", "A", "A", "B", "B", "C"], name="category")
    stats = compute_categorical_stats(series, row_count=len(series))

    assert stats.cardinality == 3
    assert stats.top_values[0].value == "A"
    assert stats.top_values[0].count == 3
    assert stats.top_values[0].percentage == round(3 / 6 * 100, 4)


def test_rare_value_count_counts_singletons() -> None:
    series = pd.Series(["A", "A", "B", "C", "D"], name="category")
    stats = compute_categorical_stats(series, row_count=len(series))
    # B, C, D each occur exactly once.
    assert stats.rare_value_count == 3


def test_nulls_excluded_from_cardinality_and_top_values() -> None:
    series = pd.Series(["A", None, "A", None, "B"], name="category")
    stats = compute_categorical_stats(series, row_count=len(series))
    assert stats.cardinality == 2
    total_top_value_count = sum(v.count for v in stats.top_values)
    assert total_top_value_count == 3  # only the 3 non-null values


def test_top_values_limited_to_ten() -> None:
    series = pd.Series([f"value_{i}" for i in range(20)], name="category")
    stats = compute_categorical_stats(series, row_count=len(series))
    assert len(stats.top_values) == 10


def test_deterministic_repeated_computation() -> None:
    series = pd.Series(["x", "y", "x", "z", "y", "x"])
    first = compute_categorical_stats(series, row_count=len(series))
    second = compute_categorical_stats(series, row_count=len(series))
    assert first == second
