"""Tests for deterministic train/test splitting."""

import pandas as pd
import pytest

from app.ml.errors import MLError
from app.ml.schemas import TaskType
from app.ml.splitting import split_dataset


def _xy(n: int = 40):
    X = pd.DataFrame({"a": range(n)})
    y = pd.Series((["a", "b"] * (n // 2))[:n])
    return X, y


class TestSplitSizes:
    def test_split_respects_test_size(self) -> None:
        X, y = _xy(40)
        X_train, X_test, y_train, y_test = split_dataset(
            X, y, TaskType.BINARY_CLASSIFICATION, 0.25, 42
        )
        assert len(X_train) == 30
        assert len(X_test) == 10

    def test_random_state_is_deterministic(self) -> None:
        X, y = _xy(40)
        first = split_dataset(X, y, TaskType.BINARY_CLASSIFICATION, 0.2, 42)
        second = split_dataset(X, y, TaskType.BINARY_CLASSIFICATION, 0.2, 42)
        assert first[0].equals(second[0])
        assert first[2].equals(second[2])

    def test_different_random_state_gives_different_split(self) -> None:
        X, y = _xy(40)
        first = split_dataset(X, y, TaskType.BINARY_CLASSIFICATION, 0.2, 1)
        second = split_dataset(X, y, TaskType.BINARY_CLASSIFICATION, 0.2, 2)
        assert not first[0].equals(second[0])


class TestStratification:
    def test_classification_splits_are_stratified(self) -> None:
        X, y = _xy(40)  # balanced 20/20
        _, _, y_train, y_test = split_dataset(X, y, TaskType.BINARY_CLASSIFICATION, 0.2, 42)
        # With a balanced target and stratification, each split keeps roughly the ratio.
        assert set(y_train.value_counts().index) == {"a", "b"}
        assert set(y_test.value_counts().index) == {"a", "b"}

    def test_regression_is_not_stratified(self) -> None:
        X = pd.DataFrame({"a": range(40)})
        y = pd.Series(range(40))
        # Should not raise even though y has no repeated values (stratify would fail).
        X_train, X_test, y_train, y_test = split_dataset(X, y, TaskType.REGRESSION, 0.2, 42)
        assert len(X_train) == 32


class TestInvalidConfiguration:
    def test_test_size_zero_rejected(self) -> None:
        X, y = _xy(40)
        with pytest.raises(MLError) as exc_info:
            split_dataset(X, y, TaskType.REGRESSION, 0.0, 42)
        assert exc_info.value.code == "invalid_split_configuration"

    def test_test_size_one_rejected(self) -> None:
        X, y = _xy(40)
        with pytest.raises(MLError) as exc_info:
            split_dataset(X, y, TaskType.REGRESSION, 1.0, 42)
        assert exc_info.value.code == "invalid_split_configuration"

    def test_test_size_too_small_for_dataset_rejected(self) -> None:
        X = pd.DataFrame({"a": range(10)})
        y = pd.Series(range(10))
        with pytest.raises(MLError) as exc_info:
            split_dataset(X, y, TaskType.REGRESSION, 0.01, 42)  # would round to 0 test rows
        assert exc_info.value.code == "invalid_split_configuration"
