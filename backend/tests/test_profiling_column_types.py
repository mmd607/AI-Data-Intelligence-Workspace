"""Unit tests for semantic type detection — golden-value tests against constructed
Series with deliberately known characteristics.
"""

import pandas as pd

from app.profiling.column_types import detect_semantic_type
from app.profiling.schemas import SemanticType


def test_integer_column_is_numeric() -> None:
    series = pd.Series([1, 2, 3, 4, 5], name="value")
    assert detect_semantic_type(series, len(series)) == SemanticType.NUMERIC


def test_float_column_is_numeric() -> None:
    series = pd.Series([1.5, 2.5, None, 4.5], name="value")
    assert detect_semantic_type(series, len(series)) == SemanticType.NUMERIC


def test_boolean_column_is_boolean() -> None:
    series = pd.Series([True, False, True, False], name="flag")
    assert detect_semantic_type(series, len(series)) == SemanticType.BOOLEAN


def test_low_cardinality_object_column_is_categorical() -> None:
    series = pd.Series(["A", "B", "A", "A", "B", "C"] * 5, name="category")
    assert detect_semantic_type(series, len(series)) == SemanticType.CATEGORICAL


def test_high_cardinality_unique_strings_is_text() -> None:
    values = [f"free text entry number {i} with unique content" for i in range(50)]
    series = pd.Series(values, name="notes")
    assert detect_semantic_type(series, len(series)) == SemanticType.TEXT


def test_iso_date_strings_are_datetime() -> None:
    series = pd.Series(["2024-01-01", "2024-02-15", "2024-03-20", "2024-04-10"], name="signup_date")
    assert detect_semantic_type(series, len(series)) == SemanticType.DATETIME


def test_plain_integer_strings_are_not_misclassified_as_datetime() -> None:
    # Guards against pandas' aggressive numeric-to-date reinterpretation.
    series = pd.Series(["100", "200", "300", "400"], name="code")
    assert detect_semantic_type(series, len(series)) == SemanticType.CATEGORICAL


def test_mostly_unparseable_dates_are_not_classified_as_datetime() -> None:
    series = pd.Series(["not a date", "also not", "still not", "nope"], name="junk")
    assert detect_semantic_type(series, len(series)) != SemanticType.DATETIME


def test_empty_series_does_not_crash_and_is_categorical() -> None:
    series = pd.Series([], name="empty", dtype=object)
    assert detect_semantic_type(series, 0) == SemanticType.CATEGORICAL


def test_native_datetime64_dtype_is_datetime() -> None:
    # Rare from a plain pd.read_csv (dates stay as strings unless explicitly parsed), but
    # a real pandas dtype the classifier must still handle correctly.
    series = pd.Series(pd.to_datetime(["2024-01-01", "2024-02-01"]), name="signup_date")
    assert detect_semantic_type(series, len(series)) == SemanticType.DATETIME


def test_dtype_with_no_matching_category_falls_back_to_unknown() -> None:
    # timedelta64 is a real pandas dtype that is neither bool, numeric, datetime64,
    # object, nor pandas' "string" dtype — the conservative UNKNOWN fallback applies.
    series = pd.Series(pd.to_timedelta(["1 days", "2 days", "3 days"]), name="duration")
    assert detect_semantic_type(series, len(series)) == SemanticType.UNKNOWN
