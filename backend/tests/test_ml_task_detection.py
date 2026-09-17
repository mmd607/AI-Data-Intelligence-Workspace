"""Tests for deterministic task-type suitability detection."""

import pandas as pd

from app.ml.schemas import TaskType
from app.ml.task_detection import (
    build_validate_target_response,
    evaluate_task_suitability,
    suggest_task,
)


def _suitable(suitabilities, task_type) -> bool:
    return next(s for s in suitabilities if s.task_type == task_type).suitable


class TestBinaryClassificationSuitability:
    def test_two_distinct_values_is_suitable(self) -> None:
        series = pd.Series(["yes", "no"] * 10)
        suitabilities = evaluate_task_suitability(series, len(series))
        assert _suitable(suitabilities, TaskType.BINARY_CLASSIFICATION) is True

    def test_three_distinct_values_is_not_binary(self) -> None:
        series = pd.Series(["a", "b", "c"] * 10)
        suitabilities = evaluate_task_suitability(series, len(series))
        assert _suitable(suitabilities, TaskType.BINARY_CLASSIFICATION) is False


class TestMulticlassClassificationSuitability:
    def test_four_distinct_values_is_suitable(self) -> None:
        series = pd.Series(["a", "b", "c", "d"] * 5)
        suitabilities = evaluate_task_suitability(series, len(series))
        assert _suitable(suitabilities, TaskType.MULTICLASS_CLASSIFICATION) is True

    def test_too_many_distinct_values_is_not_multiclass(self) -> None:
        series = pd.Series([f"v{i}" for i in range(25)] * 2)
        suitabilities = evaluate_task_suitability(series, len(series))
        assert _suitable(suitabilities, TaskType.MULTICLASS_CLASSIFICATION) is False


class TestRegressionSuitability:
    def test_numeric_with_many_values_is_suitable(self) -> None:
        series = pd.Series(range(20))
        suitabilities = evaluate_task_suitability(series, len(series))
        assert _suitable(suitabilities, TaskType.REGRESSION) is True

    def test_categorical_target_is_not_suitable_for_regression(self) -> None:
        series = pd.Series(["a", "b", "c"] * 10)
        suitabilities = evaluate_task_suitability(series, len(series))
        assert _suitable(suitabilities, TaskType.REGRESSION) is False

    def test_two_valued_numeric_target_is_not_regression(self) -> None:
        series = pd.Series([0, 1] * 10)
        suitabilities = evaluate_task_suitability(series, len(series))
        assert _suitable(suitabilities, TaskType.REGRESSION) is False


class TestInsufficientRows:
    def test_below_minimum_rows_all_tasks_unsuitable(self) -> None:
        series = pd.Series([1, 2, 3])  # well below MIN_ROWS_FOR_TRAINING
        suitabilities = evaluate_task_suitability(series, len(series))
        assert all(not s.suitable for s in suitabilities)
        assert all("non-null target value" in s.reason for s in suitabilities)

    def test_nulls_do_not_count_toward_minimum_rows(self) -> None:
        # 20 total rows but only 5 non-null — below the minimum despite row_count=20.
        series = pd.Series([1, 2, 3, 4, 5] + [None] * 15)
        suitabilities = evaluate_task_suitability(series, len(series))
        assert all(not s.suitable for s in suitabilities)


class TestSuggestTask:
    def test_prefers_binary_over_regression(self) -> None:
        series = pd.Series([0, 1] * 10)  # numeric but only 2 values
        suitabilities = evaluate_task_suitability(series, len(series))
        assert suggest_task(suitabilities) == TaskType.BINARY_CLASSIFICATION

    def test_returns_none_when_nothing_suitable(self) -> None:
        series = pd.Series([f"unique_{i}" for i in range(30)])
        suitabilities = evaluate_task_suitability(series, len(series))
        assert suggest_task(suitabilities) is None


class TestBuildValidateTargetResponse:
    def test_response_is_always_labeled_a_suggestion(self) -> None:
        series = pd.Series(["yes", "no"] * 10)
        response = build_validate_target_response("ds1", "target", series, len(series))
        assert response.is_suggestion is True
        assert response.suggested_task == TaskType.BINARY_CLASSIFICATION

    def test_observed_facts_match_the_series(self) -> None:
        series = pd.Series(["a", "a", None, "b"] * 5)
        response = build_validate_target_response("ds1", "target", series, len(series))
        assert response.observed.row_count == 20
        assert response.observed.null_count == 5
        assert response.observed.non_null_count == 15
        assert response.observed.unique_count == 2
