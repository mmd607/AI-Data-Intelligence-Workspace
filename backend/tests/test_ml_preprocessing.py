"""Tests for feature selection and preprocessing pipeline construction, including the
leakage-prevention exclusions (duplicate-of-target, constant columns, unsupported types).
"""

import numpy as np
import pandas as pd

from app.ml.preprocessing import build_preprocessing_summary, build_preprocessor, select_features


class TestFeatureSelection:
    def test_numeric_and_categorical_split_correctly(self) -> None:
        df = pd.DataFrame(
            {
                "age": [25, 30, 35, 40],
                "category": ["a", "b", "a", "b"],
                "target": [0, 1, 0, 1],
            }
        )
        selection = select_features(df, "target", len(df))
        assert selection.numeric_features == ["age"]
        assert selection.categorical_features == ["category"]
        assert selection.excluded_columns == []

    def test_target_column_never_appears_in_features(self) -> None:
        df = pd.DataFrame({"target": [0, 1, 0, 1], "x": [1, 2, 3, 4]})
        selection = select_features(df, "target", len(df))
        assert "target" not in selection.feature_columns

    def test_duplicate_of_target_is_excluded(self) -> None:
        df = pd.DataFrame({"target": [1, 2, 3, 4], "target_copy": [1, 2, 3, 4], "x": [5, 6, 7, 8]})
        selection = select_features(df, "target", len(df))
        assert "target_copy" not in selection.feature_columns
        reasons = {c.column: c.reason for c in selection.excluded_columns}
        assert reasons["target_copy"] == "duplicate_of_target"

    def test_constant_column_is_excluded(self) -> None:
        df = pd.DataFrame({"target": [1, 2, 3, 4], "always_same": ["x"] * 4})
        selection = select_features(df, "target", len(df))
        assert "always_same" not in selection.feature_columns
        reasons = {c.column: c.reason for c in selection.excluded_columns}
        assert reasons["always_same"] == "constant_column"

    def test_text_and_datetime_columns_are_excluded(self) -> None:
        df = pd.DataFrame(
            {
                "target": [1, 2, 3, 4] * 5,
                "notes": [f"free text entry {i} with unique wording" for i in range(20)],
                "signup_date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"] * 5,
            }
        )
        selection = select_features(df, "target", len(df))
        assert "notes" not in selection.feature_columns
        assert "signup_date" not in selection.feature_columns
        reasons = {c.column: c.reason for c in selection.excluded_columns}
        assert reasons["notes"].startswith("unsupported_semantic_type:")
        assert reasons["signup_date"].startswith("unsupported_semantic_type:")

    def test_boolean_column_is_treated_as_categorical(self) -> None:
        df = pd.DataFrame({"target": [1, 2, 3, 4], "flag": [True, False, True, False]})
        selection = select_features(df, "target", len(df))
        assert "flag" in selection.categorical_features


class TestPreprocessorFitTransform:
    def test_fits_and_transforms_numeric_and_categorical_features(self) -> None:
        df = pd.DataFrame(
            {
                "age": [25.0, np.nan, 35.0, 40.0],
                "category": ["a", "b", None, "b"],
                "target": [0, 1, 0, 1],
            }
        )
        selection = select_features(df, "target", len(df))
        preprocessor = build_preprocessor(selection)

        transformed = preprocessor.fit_transform(df[selection.feature_columns])
        assert transformed.shape[0] == 4  # no rows dropped despite missing values

    def test_infinite_values_do_not_crash_the_pipeline(self) -> None:
        df = pd.DataFrame(
            {
                "ratio": [1.0, 2.0, float("inf"), 4.0],
                "target": [0, 1, 0, 1],
            }
        )
        selection = select_features(df, "target", len(df))
        preprocessor = build_preprocessor(selection)
        transformed = preprocessor.fit_transform(df[selection.feature_columns])
        assert np.isfinite(transformed).all()  # inf was imputed away, not left in

    def test_unseen_category_at_transform_time_does_not_crash(self) -> None:
        train_df = pd.DataFrame({"category": ["a", "b", "a", "b"], "target": [0, 1, 0, 1]})
        selection = select_features(train_df, "target", len(train_df))
        preprocessor = build_preprocessor(selection)
        preprocessor.fit(train_df[selection.feature_columns])

        test_df = pd.DataFrame({"category": ["c"]})  # unseen at fit time
        transformed = preprocessor.transform(test_df)
        assert transformed.shape[0] == 1


class TestPreprocessingSummary:
    def test_summary_reflects_selected_features(self) -> None:
        df = pd.DataFrame(
            {"age": [1, 2, 3, 4], "category": ["a", "b", "a", "b"], "target": [0, 1, 0, 1]}
        )
        selection = select_features(df, "target", len(df))
        summary = build_preprocessing_summary(selection)
        assert summary.numeric_features == ["age"]
        assert summary.categorical_features == ["category"]
        assert "scaling" in summary.numeric_transform
        assert "encoding" in summary.categorical_transform

    def test_summary_reports_n_a_for_absent_feature_groups(self) -> None:
        df = pd.DataFrame({"age": [1, 2, 3, 4], "target": [0, 1, 0, 1]})
        selection = select_features(df, "target", len(df))
        summary = build_preprocessing_summary(selection)
        assert summary.categorical_transform == "n/a"
