"""Tests for deterministic evidence construction — correctness, determinism, size caps,
and error handling. No provider involved here at all."""

import pandas as pd
import pytest

from app.ai.errors import AIError
from app.ai.evidence import (
    build_column_insight_evidence,
    build_correlation_explanation_evidence,
    build_dataset_summary_evidence,
    build_ml_explanation_evidence,
    build_quality_explanation_evidence,
    strip_intent,
)


def _df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": [25, 30, None, 40, 22, 22, 60, 35, 29, 50],
            "category": ["A", "B", "A", "C", "A", "A", "B", "A", "A", "C"],
        }
    )


class TestStripIntent:
    def test_removes_only_the_intent_key(self) -> None:
        evidence = {"_intent": "dataset_summary", "row_count": 10}
        result = strip_intent(evidence)
        assert "_intent" not in result
        assert result == {"row_count": 10}


class TestDatasetSummaryEvidence:
    def test_contains_expected_fields(self) -> None:
        evidence = build_dataset_summary_evidence("ds1", _df())
        assert evidence["_intent"] == "dataset_summary"
        assert evidence["row_count"] == 10
        assert evidence["column_count"] == 2
        assert evidence["duplicate_row_percentage"] == 10.0
        assert len(evidence["columns"]) == 2

    def test_deterministic_repeated_computation(self) -> None:
        df = _df()
        first = strip_intent(build_dataset_summary_evidence("ds1", df))
        second = strip_intent(build_dataset_summary_evidence("ds1", df))
        assert first == second


class TestQualityExplanationEvidence:
    def test_contains_real_findings(self) -> None:
        evidence = build_quality_explanation_evidence("ds1", _df())
        assert evidence["finding_count"] == len(evidence["findings"])
        codes = {f["code"] for f in evidence["findings"]}
        assert "duplicate_rows" in codes

    def test_caps_finding_count_sent_as_evidence(self) -> None:
        # 30 constant columns -> 30 constant_column findings, capped by MAX_QUALITY_FINDINGS.
        columns = {f"c{i}": ["x"] * 20 for i in range(30)}
        df = pd.DataFrame(columns)
        evidence = build_quality_explanation_evidence("ds1", df)
        assert len(evidence["findings"]) <= 20


class TestColumnInsightEvidence:
    def test_numeric_column(self) -> None:
        evidence = build_column_insight_evidence("ds1", _df(), "age")
        assert evidence["semantic_type"] == "numeric"
        assert evidence["numeric_stats"] is not None
        assert evidence["categorical_stats"] is None

    def test_unknown_column_raises_structured_error(self) -> None:
        with pytest.raises(AIError) as exc_info:
            build_column_insight_evidence("ds1", _df(), "does_not_exist")
        assert exc_info.value.code == "column_not_found"
        assert exc_info.value.status_code == 404


class TestCorrelationExplanationEvidence:
    def test_pairs_sorted_by_absolute_strength(self) -> None:
        df = pd.DataFrame({"a": range(20), "b": range(20), "c": [1, 2] * 10})
        evidence = build_correlation_explanation_evidence("ds1", df)
        if len(evidence["pairs"]) > 1:
            coefficients = [abs(p["coefficient"]) for p in evidence["pairs"]]
            assert coefficients == sorted(coefficients, reverse=True)

    def test_insufficient_data_reported_not_crashed(self) -> None:
        df = pd.DataFrame({"only_col": range(10)})
        evidence = build_correlation_explanation_evidence("ds1", df)
        assert evidence["status"] == "insufficient_data"
        assert evidence["pairs"] == []


class TestMlExplanationEvidence:
    def test_valid_ml_result_preserved_exactly(self) -> None:
        ml_result = {
            "task_type": "regression",
            "target_column": "price",
            "model_name": "linear_regression",
            "feature_columns": ["a", "b"],
            "train_size": 80,
            "test_size_actual": 20,
            "metrics": {"rmse": 12.34, "r2": 0.91},
        }
        evidence = build_ml_explanation_evidence(ml_result)
        assert evidence["metrics"] == ml_result["metrics"]
        assert evidence["target_column"] == ml_result["target_column"]
        assert evidence["task_type"] == ml_result["task_type"]

    def test_missing_ml_result_raises(self) -> None:
        with pytest.raises(AIError) as exc_info:
            build_ml_explanation_evidence(None)
        assert exc_info.value.code == "ml_result_required"

    def test_malformed_ml_result_raises(self) -> None:
        with pytest.raises(AIError) as exc_info:
            build_ml_explanation_evidence({"task_type": "regression"})  # missing required fields
        assert exc_info.value.code == "ml_result_malformed"
