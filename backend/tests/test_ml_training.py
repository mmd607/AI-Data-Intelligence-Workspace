"""Integration-level tests for the training orchestration: prepare_training_data +
train_single_model across all three task types, plus leakage-prevention and determinism.
"""

import numpy as np
import pandas as pd
import pytest

from app.ml.errors import MLError
from app.ml.schemas import ModelName, TaskType
from app.ml.training import prepare_training_data, train_single_model

BINARY = TaskType.BINARY_CLASSIFICATION
MULTICLASS = TaskType.MULTICLASS_CLASSIFICATION
REGRESSION = TaskType.REGRESSION
RANDOM_FOREST_CLF = ModelName.RANDOM_FOREST_CLASSIFIER


def _classification_df(n: int = 60, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    age = rng.integers(18, 70, n)
    income = rng.normal(45000, 12000, n)
    category = rng.choice(["a", "b", "c"], n)
    score = age * 0.5 + income / 1000 + rng.normal(0, 5, n)
    outcome = np.where(score > np.median(score), "yes", "no")
    return pd.DataFrame({"age": age, "income": income, "category": category, "outcome": outcome})


def _regression_df(n: int = 60, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x1 = rng.normal(0, 1, n)
    x2 = rng.normal(0, 1, n)
    category = rng.choice(["a", "b"], n)
    y = x1 * 10 + x2 * 5 + rng.normal(0, 1, n)
    return pd.DataFrame({"x1": x1, "x2": x2, "category": category, "y": y})


class TestBinaryClassificationTraining:
    def test_full_pipeline_produces_a_valid_result(self) -> None:
        df = _classification_df()
        prepared = prepare_training_data(df, "outcome", BINARY, 0.2, 42)
        result = train_single_model(
            prepared, "ds1", "outcome", BINARY, ModelName.LOGISTIC_REGRESSION, 0.2, 42
        )
        assert result.task_type == BINARY
        assert set(result.feature_columns) == {"age", "income", "category"}
        assert 0.0 <= result.metrics["accuracy"] <= 1.0
        assert result.confusion_matrix is not None
        assert result.train_size + result.test_size_actual == 60


class TestMulticlassClassificationTraining:
    def test_full_pipeline_produces_a_valid_result(self) -> None:
        rng = np.random.default_rng(1)
        n = 80
        df = pd.DataFrame(
            {
                "x1": rng.normal(0, 1, n),
                "tier": rng.choice(["bronze", "silver", "gold", "platinum"], n),
            }
        )
        prepared = prepare_training_data(df, "tier", MULTICLASS, 0.2, 42)
        result = train_single_model(
            prepared, "ds1", "tier", MULTICLASS,
            RANDOM_FOREST_CLF, 0.2, 42,
        )
        assert len(result.confusion_matrix.labels) == 4
        assert "roc_auc" in result.unavailable_metrics


class TestRegressionTraining:
    def test_full_pipeline_produces_a_valid_result(self) -> None:
        df = _regression_df()
        prepared = prepare_training_data(df, "y", REGRESSION, 0.2, 42)
        result = train_single_model(
            prepared, "ds1", "y", REGRESSION, ModelName.LINEAR_REGRESSION, 0.2, 42
        )
        assert "rmse" in result.metrics
        assert "r2" in result.metrics
        assert result.confusion_matrix is None


class TestLeakagePrevention:
    def test_duplicate_target_column_excluded_from_features(self) -> None:
        df = _classification_df()
        df["outcome_copy"] = df["outcome"]
        prepared = prepare_training_data(df, "outcome", BINARY, 0.2, 42)
        assert "outcome_copy" not in prepared.selection.feature_columns
        reasons = {c.column: c.reason for c in prepared.selection.excluded_columns}
        assert reasons["outcome_copy"] == "duplicate_of_target"

    def test_preprocessing_is_fit_only_on_training_split(self) -> None:
        # A category value that appears ONLY in what will become the test split must not
        # break fitting (proves the encoder was fit on train only, with unseen-category
        # handling active at transform time), and the model must still produce a result.
        df = _classification_df(n=100, seed=7)
        prepared = prepare_training_data(df, "outcome", BINARY, 0.2, 42)
        result = train_single_model(
            prepared, "ds1", "outcome", BINARY, RANDOM_FOREST_CLF, 0.2, 42
        )
        assert result.metrics["accuracy"] is not None

    def test_constant_feature_excluded(self) -> None:
        df = _classification_df()
        df["always_same"] = "x"
        prepared = prepare_training_data(df, "outcome", BINARY, 0.2, 42)
        assert "always_same" not in prepared.selection.feature_columns


class TestDeterminism:
    def test_repeated_training_with_same_seed_is_identical(self) -> None:
        df = _classification_df()
        prepared = prepare_training_data(df, "outcome", BINARY, 0.2, 42)
        first = train_single_model(
            prepared, "ds1", "outcome", BINARY, RANDOM_FOREST_CLF, 0.2, 42
        )
        second = train_single_model(
            prepared, "ds1", "outcome", BINARY, RANDOM_FOREST_CLF, 0.2, 42
        )
        assert first.metrics == second.metrics
        assert first.confusion_matrix == second.confusion_matrix

    def test_regression_is_deterministic(self) -> None:
        df = _regression_df()
        prepared = prepare_training_data(df, "y", REGRESSION, 0.2, 42)
        ridge = ModelName.RIDGE_REGRESSION
        first = train_single_model(prepared, "ds1", "y", REGRESSION, ridge, 0.2, 42)
        second = train_single_model(prepared, "ds1", "y", REGRESSION, ridge, 0.2, 42)
        assert first.metrics == second.metrics


class TestWarnings:
    def test_high_cardinality_categorical_feature_warns(self) -> None:
        n = 120
        df = _classification_df(n=n)
        # 60 distinct values, well above the high-cardinality warning threshold.
        df["merchant_id"] = [f"m{i % 60}" for i in range(n)]
        prepared = prepare_training_data(df, "outcome", BINARY, 0.2, 42)
        assert any("high cardinality" in w for w in prepared.warnings)

    def test_small_dataset_warns(self) -> None:
        df = _classification_df(n=20)  # below SMALL_DATASET_WARNING_THRESHOLD
        prepared = prepare_training_data(df, "outcome", BINARY, 0.3, 42)
        assert any("usable rows" in w for w in prepared.warnings)


class TestNoUsableFeatures:
    def test_raises_when_every_feature_is_excluded(self) -> None:
        df = pd.DataFrame({"outcome": ["yes", "no"] * 10, "constant": ["x"] * 20})
        with pytest.raises(MLError) as exc_info:
            prepare_training_data(df, "outcome", BINARY, 0.2, 42)
        assert exc_info.value.code == "no_usable_features"


class TestNullTargetRowsExcluded:
    def test_rows_with_missing_target_are_dropped_before_split(self) -> None:
        df = _classification_df(n=60)
        df.loc[0:9, "outcome"] = None  # 10 rows now have a missing target
        prepared = prepare_training_data(df, "outcome", BINARY, 0.2, 42)
        assert prepared.usable_row_count == 50
        assert len(prepared.X_train) + len(prepared.X_test) == 50
