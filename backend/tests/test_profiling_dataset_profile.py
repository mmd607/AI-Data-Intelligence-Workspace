"""Tests for dataset-level profile aggregation."""

import pandas as pd

from app.profiling.dataset_profile import build_dataset_profile


def test_row_and_column_counts() -> None:
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    profile = build_dataset_profile("ds1", df)
    assert profile.row_count == 3
    assert profile.column_count == 2
    assert len(profile.columns) == 2
    assert profile.memory_usage_bytes > 0


def test_duplicate_row_percentage() -> None:
    df = pd.DataFrame({"a": [1, 1, 2, 3]})
    profile = build_dataset_profile("ds1", df)
    assert profile.duplicate_row_count == 1
    assert profile.duplicate_row_percentage == 25.0


def test_missing_summary_aggregation() -> None:
    df = pd.DataFrame({"a": [1, None, 3, None], "b": [1, 2, 3, 4]})
    profile = build_dataset_profile("ds1", df)
    # 8 total cells, 2 missing.
    assert profile.missing.total_missing_cells == 2
    assert profile.missing.missing_percentage == 25.0
    assert profile.missing.columns_with_missing == 1


def test_zero_row_dataset_does_not_crash() -> None:
    df = pd.DataFrame({"a": pd.Series([], dtype="float64"), "b": pd.Series([], dtype=object)})
    profile = build_dataset_profile("ds1", df)
    assert profile.row_count == 0
    assert profile.duplicate_row_percentage == 0.0
    assert profile.missing.missing_percentage == 0.0
    assert len(profile.columns) == 2


def test_deterministic_repeated_computation() -> None:
    df = pd.DataFrame({"a": [1, 2, None], "b": ["x", "y", "x"]})
    first = build_dataset_profile("ds1", df)
    second = build_dataset_profile("ds1", df)
    # generated_at legitimately differs between calls (it's a real timestamp) — compare
    # everything else, which must be byte-for-byte identical.
    assert first.model_dump(exclude={"generated_at"}) == second.model_dump(exclude={"generated_at"})
