"""Tests for the deterministic data-quality findings engine."""

import pandas as pd

from app.profiling.quality import build_quality_summary


def _codes(summary) -> set[str]:
    return {f.code for f in summary.findings}


def test_clean_dataset_has_zero_findings() -> None:
    df = pd.DataFrame({"id": [1, 2, 3, 4], "value": [10.0, 20.0, 30.0, 40.0]})
    summary = build_quality_summary("ds1", df)
    assert summary.findings == []
    assert summary.finding_count == 0


def test_duplicate_rows_detected() -> None:
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    summary = build_quality_summary("ds1", df)
    assert "duplicate_rows" in _codes(summary)
    finding = next(f for f in summary.findings if f.code == "duplicate_rows")
    assert finding.metric == 1


def test_missing_values_finding_present_and_warning_severity() -> None:
    # 3 of 8 cells missing (2 columns x 4 rows) = 37.5% overall -> warning, not critical.
    df = pd.DataFrame({"a": [1, None, None, None], "b": [1, 2, 3, 4]})
    summary = build_quality_summary("ds1", df)
    finding = next(f for f in summary.findings if f.code == "missing_values")
    assert finding.severity.value == "warning"
    assert "column_high_missing" in _codes(summary)


def test_missing_values_finding_is_critical_above_fifty_percent() -> None:
    # 6 of 8 cells missing (2 columns x 4 rows) = 75% overall -> critical.
    df = pd.DataFrame({"a": [None, None, None, None], "b": [1, None, None, 4]})
    summary = build_quality_summary("ds1", df)
    finding = next(f for f in summary.findings if f.code == "missing_values")
    assert finding.severity.value == "critical"


def test_constant_column_detected() -> None:
    df = pd.DataFrame({"flag": ["true"] * 10, "value": range(10)})
    summary = build_quality_summary("ds1", df)
    finding = next(f for f in summary.findings if f.code == "constant_column")
    assert finding.column == "flag"


def test_near_constant_column_detected_at_threshold() -> None:
    df = pd.DataFrame({"mostly_same": ["x"] * 19 + ["y"], "id": range(20)})
    summary = build_quality_summary("ds1", df)
    assert "near_constant_column" in _codes(summary)


def test_high_cardinality_categorical_detected() -> None:
    df = pd.DataFrame({"code": [f"id_{i}" for i in range(10)]})
    summary = build_quality_summary("ds1", df)
    assert "high_cardinality_categorical" in _codes(summary)


def test_mixed_type_column_detected() -> None:
    df = pd.DataFrame({"value": ["1", "2", "3", "not-a-number", "5", "6", "7", "8", "9", "text"]})
    summary = build_quality_summary("ds1", df)
    assert "mixed_type_column" in _codes(summary)


def test_infinite_values_detected_as_critical() -> None:
    df = pd.DataFrame({"ratio": [1.0, 2.0, float("inf"), 3.0]})
    summary = build_quality_summary("ds1", df)
    finding = next(f for f in summary.findings if f.code == "infinite_values")
    assert finding.severity.value == "critical"
    assert finding.metric == 1


def test_unexpected_negative_values_in_presumed_nonnegative_column() -> None:
    df = pd.DataFrame({"age": [25, -5, 30, 40]})
    summary = build_quality_summary("ds1", df)
    assert "unexpected_negative_values" in _codes(summary)


def test_negative_values_in_unrelated_column_name_not_flagged() -> None:
    df = pd.DataFrame({"temperature": [25, -5, 30, 40]})
    summary = build_quality_summary("ds1", df)
    assert "unexpected_negative_values" not in _codes(summary)


def test_invalid_datetime_values_detected() -> None:
    # 9 valid dates + 1 invalid = 90% parse rate, at the classifier's detection threshold,
    # so the column is still (correctly) classified as DATETIME overall.
    dates = [f"2024-{month:02d}-01" for month in range(1, 10)] + ["not-a-date"]
    df = pd.DataFrame({"signup_date": dates})
    summary = build_quality_summary("ds1", df)
    assert "invalid_datetime_values" in _codes(summary)


def test_empty_dataset_zero_rows_is_info_not_error() -> None:
    df = pd.DataFrame({"a": pd.Series([], dtype="float64"), "b": pd.Series([], dtype=object)})
    summary = build_quality_summary("ds1", df)
    assert "empty_dataset" in _codes(summary)


def test_zero_columns_returns_critical_finding_without_crashing() -> None:
    df = pd.DataFrame(index=range(3))
    summary = build_quality_summary("ds1", df)
    assert _codes(summary) == {"zero_columns"}


def test_deterministic_repeated_computation() -> None:
    df = pd.DataFrame({"a": [1, 1, 2, None], "b": ["x", "x", "y", "z"]})
    first = build_quality_summary("ds1", df)
    second = build_quality_summary("ds1", df)
    assert [f.code for f in first.findings] == [f.code for f in second.findings]
