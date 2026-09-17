"""Tests for deterministic Pearson correlation, including the explicit
insufficient-data paths (never a crash, never a silent empty result)."""

import pandas as pd

from app.profiling.correlation import compute_correlation


def test_perfect_positive_correlation() -> None:
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]})
    result = compute_correlation("ds1", df, minimum_observations=3)

    assert result.status == "computed"
    assert len(result.pairs) == 1
    assert result.pairs[0].column_a == "x"
    assert result.pairs[0].column_b == "y"
    assert abs(result.pairs[0].coefficient - 1.0) < 1e-9
    assert result.pairs[0].observations == 5


def test_perfect_negative_correlation() -> None:
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 8, 6, 4, 2]})
    result = compute_correlation("ds1", df, minimum_observations=3)
    assert abs(result.pairs[0].coefficient - (-1.0)) < 1e-9


def test_fewer_than_two_numeric_columns_is_insufficient_data() -> None:
    df = pd.DataFrame({"x": [1, 2, 3], "category": ["a", "b", "c"]})
    result = compute_correlation("ds1", df)
    assert result.status == "insufficient_data"
    assert result.pairs == []
    assert result.eligible_columns == ["x"]
    assert result.message is not None


def test_boolean_columns_excluded_from_numeric_eligibility() -> None:
    df = pd.DataFrame({"flag": [True, False, True], "x": [1, 2, 3]})
    result = compute_correlation("ds1", df)
    assert "flag" not in result.eligible_columns
    assert result.status == "insufficient_data"  # only 1 real numeric column


def test_missing_values_handled_pairwise_not_dataset_wide() -> None:
    # x has a null at index 2, y has a null at index 0 — non-overlapping nulls.
    # Pairwise dropna over (x, y) leaves indices 1 and 3 usable = 2 observations.
    df = pd.DataFrame({"x": [1, 2, None, 4], "y": [None, 20, 30, 40]})
    result = compute_correlation("ds1", df, minimum_observations=2)
    assert result.status == "computed"
    assert result.pairs[0].observations == 2


def test_insufficient_observations_for_only_pair_is_insufficient_data() -> None:
    df = pd.DataFrame({"x": [1, None, None, None], "y": [None, None, None, 4]})
    result = compute_correlation("ds1", df, minimum_observations=3)
    assert result.status == "insufficient_data"
    assert result.pairs == []


def test_zero_variance_column_pair_is_skipped_not_crashed() -> None:
    df = pd.DataFrame({"x": [5, 5, 5, 5, 5], "y": [1, 2, 3, 4, 5]})
    result = compute_correlation("ds1", df, minimum_observations=3)
    assert result.status == "insufficient_data"
    assert result.pairs == []


def test_deterministic_ordering_and_repeated_computation() -> None:
    df = pd.DataFrame({"a": [1, 2, 3, 4], "b": [4, 3, 2, 1], "c": [1, 1, 2, 2]})
    first = compute_correlation("ds1", df, minimum_observations=3)
    second = compute_correlation("ds1", df, minimum_observations=3)
    assert [((p.column_a, p.column_b)) for p in first.pairs] == [
        ((p.column_a, p.column_b)) for p in second.pairs
    ]
    assert first.pairs == second.pairs
