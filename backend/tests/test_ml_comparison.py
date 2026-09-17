"""Tests for multi-model comparison under an identical split."""

import numpy as np
import pandas as pd

from app.ml.comparison import compare_models
from app.ml.schemas import ModelName, TaskType


def _classification_df(n: int = 60, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    age = rng.integers(18, 70, n)
    income = rng.normal(45000, 12000, n)
    score = age * 0.5 + income / 1000 + rng.normal(0, 5, n)
    outcome = np.where(score > np.median(score), "yes", "no")
    return pd.DataFrame({"age": age, "income": income, "outcome": outcome})


class TestCompareModels:
    def test_returns_one_result_per_model(self) -> None:
        df = _classification_df()
        result = compare_models(
            df, "ds1", "outcome", TaskType.BINARY_CLASSIFICATION,
            [ModelName.LOGISTIC_REGRESSION, ModelName.RANDOM_FOREST_CLASSIFIER], 0.2, 42,
        )
        assert len(result.results) == 2
        assert {r.model_name for r in result.results} == {
            ModelName.LOGISTIC_REGRESSION, ModelName.RANDOM_FOREST_CLASSIFIER
        }

    def test_all_models_share_the_identical_split(self) -> None:
        df = _classification_df()
        result = compare_models(
            df, "ds1", "outcome", TaskType.BINARY_CLASSIFICATION,
            [ModelName.LOGISTIC_REGRESSION, ModelName.RANDOM_FOREST_CLASSIFIER], 0.2, 42,
        )
        sizes = {(r.train_size, r.test_size_actual) for r in result.results}
        assert len(sizes) == 1  # identical split sizes across every model

    def test_result_has_no_aggregate_score_or_winner_field(self) -> None:
        df = _classification_df()
        result = compare_models(
            df, "ds1", "outcome", TaskType.BINARY_CLASSIFICATION,
            [ModelName.LOGISTIC_REGRESSION, ModelName.RANDOM_FOREST_CLASSIFIER], 0.2, 42,
        )
        result_fields = set(result.model_dump().keys())
        assert "winner" not in result_fields
        assert "best_model" not in result_fields
        assert "score" not in result_fields
        assert "ai_score" not in result_fields

    def test_single_model_comparison_works(self) -> None:
        df = _classification_df()
        result = compare_models(
            df, "ds1", "outcome", TaskType.BINARY_CLASSIFICATION,
            [ModelName.LOGISTIC_REGRESSION], 0.2, 42,
        )
        assert len(result.results) == 1
