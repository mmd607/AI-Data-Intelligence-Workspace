"""Tests for deterministic-first question routing — the LLM narrates, it never computes."""

import pandas as pd

from app.ai.routing import route_question
from app.ai.schemas import QuestionCategory


def _df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": [25, 30, 35, 40, 45, 50, 55, 60, 65, 70],
            "income": [50000, 55000, 60000, 65000, 70000, 75000, 80000, 85000, 90000, 95000],
            "category": ["A", "B", "A", "C", "A", "A", "B", "A", "A", "C"],
        }
    )


class TestDuplicateQuestions:
    def test_duplicate_count_question_resolved_deterministically(self) -> None:
        df = pd.DataFrame({"a": [1, 1, 2, 3]})
        routed = route_question("How many rows are duplicated?", df, "ds1", None)
        assert routed.category == QuestionCategory.DETERMINISTIC_LOOKUP
        assert "1" in routed.resolved_answer


class TestMissingValueQuestions:
    def test_which_column_has_most_missing_values(self) -> None:
        df = pd.DataFrame({"a": [1, None, None, 4], "b": [1, 2, 3, 4]})
        routed = route_question("What columns have the most missing values?", df, "ds1", None)
        assert routed.category == QuestionCategory.DETERMINISTIC_LOOKUP
        assert "'a'" in routed.resolved_answer

    def test_no_columns_at_all_is_unsupported(self) -> None:
        df = pd.DataFrame()
        routed = route_question("Which column has the most missing values?", df, "ds1", None)
        assert routed.category == QuestionCategory.UNSUPPORTED


class TestCorrelationQuestions:
    def test_strongest_correlation_resolved(self) -> None:
        df = pd.DataFrame({"x": range(20), "y": range(20), "z": [1, 2] * 10})
        routed = route_question("Which features are strongly correlated?", df, "ds1", None)
        assert routed.category == QuestionCategory.DETERMINISTIC_LOOKUP
        assert routed.resolved_answer is not None

    def test_no_correlation_data_is_unsupported(self) -> None:
        df = pd.DataFrame({"only_numeric": range(10)})
        routed = route_question("Which features are strongly correlated?", df, "ds1", None)
        assert routed.category == QuestionCategory.UNSUPPORTED


class TestColumnStatisticQuestions:
    def test_average_of_named_column_resolved_exactly(self) -> None:
        df = _df()
        routed = route_question("What is the average value of age?", df, "ds1", None)
        assert routed.category == QuestionCategory.DETERMINISTIC_LOOKUP
        assert str(df["age"].mean()) in routed.resolved_answer

    def test_unknown_column_name_does_not_match(self) -> None:
        df = _df()
        routed = route_question(
            "What is the average value of nonexistent_column?", df, "ds1", None
        )
        assert routed.category != QuestionCategory.DETERMINISTIC_LOOKUP

    def test_non_numeric_column_statistic_does_not_resolve_deterministically(self) -> None:
        df = _df()
        routed = route_question("What is the average value of category?", df, "ds1", None)
        assert routed.category != QuestionCategory.DETERMINISTIC_LOOKUP

    def test_undefined_statistic_falls_through(self) -> None:
        # A single-row numeric column has an undefined standard deviation (None) — the
        # matched statistic exists but its value can't be reported, so this must not
        # produce a deterministic answer for a value that isn't actually available.
        df = pd.DataFrame({"age": [42], "category": ["A"]})
        routed = route_question(
            "What is the standard deviation of age?", df, "ds1", None
        )
        assert routed.category != QuestionCategory.DETERMINISTIC_LOOKUP


class TestMlPerformanceQuestions:
    def test_model_performance_with_ml_result_resolved(self) -> None:
        df = _df()
        ml_result = {"model_name": "logistic_regression", "metrics": {"f1": 0.81, "accuracy": 0.85}}
        routed = route_question("How did the baseline model perform?", df, "ds1", ml_result)
        assert routed.category == QuestionCategory.DETERMINISTIC_LOOKUP
        assert "0.81" in routed.resolved_answer

    def test_explain_f1_score_uses_supplied_metric(self) -> None:
        df = _df()
        ml_result = {"model_name": "random_forest_classifier", "metrics": {"f1": 0.81}}
        routed = route_question("Explain the model's F1 score.", df, "ds1", ml_result)
        assert routed.category == QuestionCategory.DETERMINISTIC_LOOKUP
        assert "0.81" in routed.resolved_answer

    def test_ml_question_without_ml_result_is_unsupported(self) -> None:
        df = _df()
        routed = route_question("What was the model's accuracy?", df, "ds1", None)
        assert routed.category == QuestionCategory.UNSUPPORTED


class TestQualityExplanationRouting:
    def test_main_quality_issues_routes_to_explanation(self) -> None:
        df = _df()
        routed = route_question("What are the main data-quality issues?", df, "ds1", None)
        assert routed.category == QuestionCategory.EXPLANATION


class TestUnmatchedQuestions:
    def test_unrecognized_question_falls_back_to_analytical_interpretation(self) -> None:
        df = _df()
        routed = route_question("Tell me something interesting about this data.", df, "ds1", None)
        assert routed.category == QuestionCategory.ANALYTICAL_INTERPRETATION


class TestDeterminism:
    def test_same_question_repeated_gives_identical_result(self) -> None:
        df = _df()
        first = route_question("How many rows are duplicated?", df, "ds1", None)
        second = route_question("How many rows are duplicated?", df, "ds1", None)
        assert first == second
