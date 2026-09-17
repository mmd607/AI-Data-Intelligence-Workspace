"""Tests for target-column validation — every structured error code and warning."""

import pandas as pd
import pytest

from app.ml.errors import MLError
from app.ml.schemas import TaskType
from app.ml.target_validation import validate_target_for_training


def _df(**columns) -> pd.DataFrame:
    return pd.DataFrame(columns)


class TestTargetExistence:
    def test_missing_column_raises_target_not_found(self) -> None:
        df = _df(a=range(20))
        with pytest.raises(MLError) as exc_info:
            validate_target_for_training(df, "does_not_exist", TaskType.REGRESSION)
        assert exc_info.value.code == "target_not_found"
        assert exc_info.value.status_code == 404


class TestAllMissingTarget:
    def test_entirely_null_target_raises(self) -> None:
        df = _df(target=[None] * 20, feature=range(20))
        with pytest.raises(MLError) as exc_info:
            validate_target_for_training(df, "target", TaskType.REGRESSION)
        assert exc_info.value.code == "target_all_missing"


class TestInsufficientRows:
    def test_too_few_non_null_targets_raises(self) -> None:
        df = _df(target=[1, 2, 3], feature=[1, 2, 3])
        with pytest.raises(MLError) as exc_info:
            validate_target_for_training(df, "target", TaskType.REGRESSION)
        assert exc_info.value.code == "insufficient_rows"

    def test_nulls_reduce_usable_count_below_minimum(self) -> None:
        # 20 rows total, but only 5 non-null targets — below MIN_ROWS_FOR_TRAINING.
        df = _df(target=[1, 2, 3, 4, 5] + [None] * 15, feature=range(20))
        with pytest.raises(MLError) as exc_info:
            validate_target_for_training(df, "target", TaskType.REGRESSION)
        assert exc_info.value.code == "insufficient_rows"


class TestSingleClassTarget:
    def test_single_class_raises_for_binary(self) -> None:
        df = _df(target=["only-value"] * 20, feature=range(20))
        with pytest.raises(MLError) as exc_info:
            validate_target_for_training(df, "target", TaskType.BINARY_CLASSIFICATION)
        assert exc_info.value.code == "single_class_target"

    def test_single_class_raises_for_multiclass(self) -> None:
        df = _df(target=["only-value"] * 20, feature=range(20))
        with pytest.raises(MLError) as exc_info:
            validate_target_for_training(df, "target", TaskType.MULTICLASS_CLASSIFICATION)
        assert exc_info.value.code == "single_class_target"


class TestCardinalityMismatch:
    def test_three_classes_rejected_for_binary(self) -> None:
        df = _df(target=["a", "b", "c"] * 10, feature=range(30))
        with pytest.raises(MLError) as exc_info:
            validate_target_for_training(df, "target", TaskType.BINARY_CLASSIFICATION)
        assert exc_info.value.code == "invalid_target_cardinality"

    def test_two_classes_rejected_for_multiclass(self) -> None:
        df = _df(target=["a", "b"] * 10, feature=range(20))
        with pytest.raises(MLError) as exc_info:
            validate_target_for_training(df, "target", TaskType.MULTICLASS_CLASSIFICATION)
        assert exc_info.value.code == "invalid_target_cardinality"

    def test_too_many_classes_rejected_for_multiclass(self) -> None:
        df = _df(target=[f"v{i}" for i in range(25)] * 2, feature=range(50))
        with pytest.raises(MLError) as exc_info:
            validate_target_for_training(df, "target", TaskType.MULTICLASS_CLASSIFICATION)
        assert exc_info.value.code == "invalid_target_cardinality"


class TestRegressionTypeCompatibility:
    def test_non_numeric_target_rejected_for_regression(self) -> None:
        df = _df(target=["a", "b", "c"] * 10, feature=range(30))
        with pytest.raises(MLError) as exc_info:
            validate_target_for_training(df, "target", TaskType.REGRESSION)
        assert exc_info.value.code == "target_type_incompatible"

    def test_numeric_target_accepted_for_regression(self) -> None:
        df = _df(target=list(range(20)), feature=range(20))
        warnings = validate_target_for_training(df, "target", TaskType.REGRESSION)
        assert warnings == []

    def test_two_valued_numeric_target_warns_for_regression(self) -> None:
        df = _df(target=[0, 1] * 10, feature=range(20))
        warnings = validate_target_for_training(df, "target", TaskType.REGRESSION)
        assert any("binary classification instead" in w for w in warnings)


class TestClassImbalance:
    def test_insufficient_class_samples_raises(self) -> None:
        # One class has only 1 sample — below MIN_SAMPLES_PER_CLASS.
        df = _df(target=["a"] * 19 + ["b"], feature=range(20))
        with pytest.raises(MLError) as exc_info:
            validate_target_for_training(df, "target", TaskType.BINARY_CLASSIFICATION)
        assert exc_info.value.code == "insufficient_class_samples"

    def test_extreme_imbalance_below_five_percent_warns(self) -> None:
        # 2 minority class samples out of 45 = 4.44%, below the 5% warning threshold,
        # while still satisfying MIN_SAMPLES_PER_CLASS so it doesn't hard-fail.
        df = _df(target=["a"] * 43 + ["b"] * 2, feature=range(45))
        warnings = validate_target_for_training(df, "target", TaskType.BINARY_CLASSIFICATION)
        assert any("imbalanced" in w for w in warnings)

    def test_balanced_classes_produce_no_warning(self) -> None:
        df = _df(target=["a"] * 10 + ["b"] * 10, feature=range(20))
        warnings = validate_target_for_training(df, "target", TaskType.BINARY_CLASSIFICATION)
        assert warnings == []
