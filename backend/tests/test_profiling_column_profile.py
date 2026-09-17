"""Tests for per-column profiling dispatch and the JSON-safety of sample values."""

import pandas as pd

from app.profiling.column_profile import profile_column
from app.profiling.schemas import SemanticType


def test_numeric_column_gets_numeric_stats_only() -> None:
    series = pd.Series([1, 2, 3, 4, 5], name="value")
    profile = profile_column(series, row_count=5)

    assert profile.semantic_type == SemanticType.NUMERIC
    assert profile.numeric_stats is not None
    assert profile.categorical_stats is None
    assert profile.datetime_stats is None
    assert profile.null_count == 0
    assert profile.unique_count == 5
    assert profile.unique_percentage == 100.0


def test_categorical_column_gets_categorical_stats_only() -> None:
    series = pd.Series(["a", "b", "a"], name="category")
    profile = profile_column(series, row_count=3)

    assert profile.semantic_type == SemanticType.CATEGORICAL
    assert profile.categorical_stats is not None
    assert profile.numeric_stats is None
    assert profile.datetime_stats is None


def test_datetime_column_gets_datetime_stats_only() -> None:
    series = pd.Series(["2024-01-01", "2024-02-01"], name="signup_date")
    profile = profile_column(series, row_count=2)

    assert profile.semantic_type == SemanticType.DATETIME
    assert profile.datetime_stats is not None
    assert profile.numeric_stats is None
    assert profile.categorical_stats is None


def test_boolean_column_gets_no_type_specific_stats() -> None:
    series = pd.Series([True, False, True], name="flag")
    profile = profile_column(series, row_count=3)

    assert profile.semantic_type == SemanticType.BOOLEAN
    assert profile.numeric_stats is None
    assert profile.categorical_stats is None
    assert profile.datetime_stats is None


def test_sample_values_are_json_safe_and_limited() -> None:
    series = pd.Series(range(20), name="value")  # numpy int64 values
    profile = profile_column(series, row_count=20)

    assert len(profile.sample_values) == 5
    for v in profile.sample_values:
        assert isinstance(v, int | float | str | bool)


def test_null_and_unique_percentages_computed_correctly() -> None:
    series = pd.Series([1, 1, None, 3], name="value")
    profile = profile_column(series, row_count=4)

    assert profile.null_count == 1
    assert profile.null_percentage == 25.0
    assert profile.unique_count == 2  # {1, 3} among non-null
    assert profile.unique_percentage == round(2 / 3 * 100, 4)


def test_empty_column_does_not_crash() -> None:
    series = pd.Series([], name="empty", dtype="float64")
    profile = profile_column(series, row_count=0)
    assert profile.null_count == 0
    assert profile.null_percentage == 0.0
    assert profile.unique_percentage == 0.0


def test_native_datetime64_column_sample_values_are_iso_strings() -> None:
    # A genuinely datetime64-dtyped column's .tolist() yields pandas.Timestamp objects —
    # _json_safe must convert them, not let them leak into the JSON response unconverted.
    series = pd.Series(pd.to_datetime(["2024-01-01", "2024-02-15"]), name="signup_date")
    profile = profile_column(series, row_count=2)

    assert profile.semantic_type == SemanticType.DATETIME
    assert profile.sample_values == ["2024-01-01T00:00:00", "2024-02-15T00:00:00"]


def test_unknown_semantic_type_column_still_produces_a_profile() -> None:
    series = pd.Series(pd.to_timedelta(["1 days", "2 days"]), name="duration")
    profile = profile_column(series, row_count=2)

    assert profile.semantic_type == SemanticType.UNKNOWN
    assert profile.numeric_stats is None
    assert profile.categorical_stats is None
    assert profile.datetime_stats is None
    assert len(profile.sample_values) == 2
    for value in profile.sample_values:
        assert isinstance(value, str)  # timedelta objects fall back to str()
