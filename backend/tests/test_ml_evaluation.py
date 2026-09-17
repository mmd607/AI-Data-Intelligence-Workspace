"""Golden-value tests for evaluation metrics, including the explicit
unavailable-metric paths (never a fabricated or mathematically invalid value)."""

import numpy as np

from app.ml.evaluation import evaluate_classification, evaluate_regression
from app.ml.schemas import TaskType

BINARY = TaskType.BINARY_CLASSIFICATION
MULTICLASS = TaskType.MULTICLASS_CLASSIFICATION


class TestClassificationEvaluation:
    def test_perfect_predictions_score_maximally(self) -> None:
        y_true = [0, 1, 0, 1, 0, 1]
        y_pred = [0, 1, 0, 1, 0, 1]
        metrics, unavailable, confusion = evaluate_classification(
            y_true, y_pred, None, BINARY
        )
        assert metrics["accuracy"] == 1.0
        assert metrics["precision"] == 1.0
        assert metrics["recall"] == 1.0
        assert metrics["f1"] == 1.0

    def test_confusion_matrix_matches_known_values(self) -> None:
        y_true = [0, 0, 1, 1]
        y_pred = [0, 1, 1, 1]  # one false positive
        _, _, confusion = evaluate_classification(y_true, y_pred, None, BINARY)
        assert confusion.labels == ["0", "1"]
        assert confusion.matrix == [[1, 1], [0, 2]]

    def test_roc_auc_computed_for_binary_with_probabilities(self) -> None:
        y_true = [0, 0, 1, 1]
        y_pred = [0, 0, 1, 1]
        y_proba = np.array([0.1, 0.2, 0.8, 0.9])
        metrics, unavailable, _ = evaluate_classification(y_true, y_pred, y_proba, BINARY)
        assert metrics["roc_auc"] == 1.0
        assert "roc_auc" not in unavailable

    def test_roc_auc_unavailable_when_probabilities_contain_nan(self) -> None:
        # A real failure mode roc_auc_score itself rejects (e.g. a degenerate model
        # producing a NaN probability) — caught and reported, never left to crash the
        # whole evaluation.
        y_true = [0, 0, 1, 1]
        y_pred = [0, 0, 1, 1]
        y_proba = np.array([0.1, np.nan, 0.8, 0.9])
        _, unavailable, _ = evaluate_classification(y_true, y_pred, y_proba, BINARY)
        assert "roc_auc" in unavailable
        assert "Could not be computed" in unavailable["roc_auc"]

    def test_roc_auc_unavailable_without_probabilities(self) -> None:
        y_true = [0, 1, 0, 1]
        y_pred = [0, 1, 0, 1]
        _, unavailable, _ = evaluate_classification(y_true, y_pred, None, BINARY)
        assert "roc_auc" in unavailable

    def test_roc_auc_unavailable_for_multiclass(self) -> None:
        y_true = ["a", "b", "c", "a"]
        y_pred = ["a", "b", "c", "a"]
        _, unavailable, _ = evaluate_classification(y_true, y_pred, None, MULTICLASS)
        assert "roc_auc" in unavailable
        assert "multiclass" in unavailable["roc_auc"]

    def test_string_labels_handled_correctly(self) -> None:
        y_true = ["cat", "dog", "cat", "dog"]
        y_pred = ["cat", "dog", "dog", "dog"]
        metrics, _, confusion = evaluate_classification(y_true, y_pred, None, BINARY)
        assert metrics["accuracy"] == 0.75
        assert confusion.labels == ["cat", "dog"]


class TestRegressionEvaluation:
    def test_perfect_predictions_score_maximally(self) -> None:
        y_true = [1.0, 2.0, 3.0, 4.0]
        y_pred = [1.0, 2.0, 3.0, 4.0]
        metrics, unavailable = evaluate_regression(y_true, y_pred)
        assert metrics["mae"] == 0.0
        assert metrics["mse"] == 0.0
        assert metrics["rmse"] == 0.0
        assert metrics["r2"] == 1.0
        assert unavailable == {}

    def test_known_errors_computed_correctly(self) -> None:
        y_true = [10.0, 20.0, 30.0]
        y_pred = [12.0, 18.0, 33.0]
        metrics, _ = evaluate_regression(y_true, y_pred)
        # errors: 2, -2, 3 -> abs: 2,2,3 -> mae=7/3
        assert abs(metrics["mae"] - (7 / 3)) < 1e-6
        # squared errors: 4,4,9 -> mse=17/3
        assert abs(metrics["mse"] - (17 / 3)) < 1e-6
        assert abs(metrics["rmse"] - (17 / 3) ** 0.5) < 1e-6

    def test_r2_unavailable_for_single_test_sample(self) -> None:
        metrics, unavailable = evaluate_regression([5.0], [4.5])
        assert "r2" not in metrics
        assert "r2" in unavailable
        assert metrics["mae"] == 0.5
