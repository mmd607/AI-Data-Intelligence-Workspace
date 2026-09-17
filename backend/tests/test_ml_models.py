"""Tests for the fixed baseline model registry."""

import pytest
from sklearn.linear_model import LinearRegression, LogisticRegression

from app.ml.errors import MLError
from app.ml.models import build_model, supported_models
from app.ml.schemas import ModelName, TaskType


class TestSupportedModels:
    def test_classification_models_available_for_binary(self) -> None:
        models = supported_models(TaskType.BINARY_CLASSIFICATION)
        assert ModelName.LOGISTIC_REGRESSION in models
        assert ModelName.RANDOM_FOREST_CLASSIFIER in models

    def test_regression_models_available(self) -> None:
        models = supported_models(TaskType.REGRESSION)
        assert ModelName.LINEAR_REGRESSION in models
        assert ModelName.RIDGE_REGRESSION in models
        assert ModelName.RANDOM_FOREST_REGRESSOR in models

    def test_model_zoo_stays_small(self) -> None:
        # Deliberate: this project explicitly does not want a large model zoo.
        assert len(supported_models(TaskType.BINARY_CLASSIFICATION)) <= 3
        assert len(supported_models(TaskType.REGRESSION)) <= 4


class TestBuildModel:
    def test_builds_the_requested_classifier(self) -> None:
        model = build_model(ModelName.LOGISTIC_REGRESSION, TaskType.BINARY_CLASSIFICATION, 42)
        assert isinstance(model, LogisticRegression)

    def test_builds_the_requested_regressor(self) -> None:
        model = build_model(ModelName.LINEAR_REGRESSION, TaskType.REGRESSION, 42)
        assert isinstance(model, LinearRegression)

    def test_classification_model_for_regression_task_raises(self) -> None:
        with pytest.raises(MLError) as exc_info:
            build_model(ModelName.LOGISTIC_REGRESSION, TaskType.REGRESSION, 42)
        assert exc_info.value.code == "invalid_model_for_task"

    def test_regression_model_for_classification_task_raises(self) -> None:
        with pytest.raises(MLError) as exc_info:
            build_model(ModelName.LINEAR_REGRESSION, TaskType.BINARY_CLASSIFICATION, 42)
        assert exc_info.value.code == "invalid_model_for_task"
