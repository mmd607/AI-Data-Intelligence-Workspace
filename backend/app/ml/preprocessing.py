"""Feature selection and preprocessing pipeline construction.

Leakage prevention is structural, not a convention: the returned `ColumnTransformer` is
only ever `.fit()` on the training split by `training.py` (never the full dataset or the
test split) — this module only builds the (unfitted) pipeline and decides which columns
participate, it never touches the actual train/test data itself.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from app.ml.schemas import ExcludedColumn, PreprocessingSummary
from app.profiling.column_types import detect_semantic_type
from app.profiling.schemas import SemanticType

NUMERIC_TRANSFORM_DESCRIPTION = "median imputation + standard scaling"
CATEGORICAL_TRANSFORM_DESCRIPTION = (
    "most-frequent imputation + one-hot encoding (unknown categories ignored)"
)

# Semantic types excluded from the feature set outright — not silently dropped, always
# reported in `excluded_columns` with a specific reason.
_UNSUPPORTED_FEATURE_TYPES = {SemanticType.TEXT, SemanticType.DATETIME, SemanticType.UNKNOWN}


@dataclass(frozen=True)
class FeatureSelection:
    numeric_features: list[str]
    categorical_features: list[str]
    excluded_columns: list[ExcludedColumn]

    @property
    def feature_columns(self) -> list[str]:
        return self.numeric_features + self.categorical_features


def select_features(df: pd.DataFrame, target_column: str, row_count: int) -> FeatureSelection:
    numeric_features: list[str] = []
    categorical_features: list[str] = []
    excluded: list[ExcludedColumn] = []

    target_series = df[target_column]

    for column in df.columns:
        if column == target_column:
            continue

        series = df[column]

        # Explicit target-leakage guard: a candidate feature that is an exact duplicate
        # of the target column would let the model "cheat" via a trivial shortcut.
        if series.equals(target_series):
            excluded.append(ExcludedColumn(column=column, reason="duplicate_of_target"))
            continue

        semantic_type = detect_semantic_type(series, row_count)

        if semantic_type in _UNSUPPORTED_FEATURE_TYPES:
            excluded.append(
                ExcludedColumn(
                    column=column,
                    reason=f"unsupported_semantic_type:{semantic_type.value}",
                )
            )
            continue

        non_null = series.dropna()
        if non_null.nunique() <= 1:
            excluded.append(ExcludedColumn(column=column, reason="constant_column"))
            continue

        if semantic_type == SemanticType.NUMERIC:
            numeric_features.append(column)
        else:  # CATEGORICAL, BOOLEAN
            categorical_features.append(column)

    return FeatureSelection(
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        excluded_columns=excluded,
    )


def _replace_infinite_with_nan(values):
    """Replace +/-inf with NaN so the numeric imputer treats them as missing, rather than
    letting them crash `StandardScaler`/tree-based estimators downstream. A plain,
    module-level function (not a lambda) so `FunctionTransformer` stays picklable.
    """
    array = np.asarray(values, dtype="float64")
    return np.where(np.isinf(array), np.nan, array)


def build_preprocessor(selection: FeatureSelection) -> ColumnTransformer:
    transformers = []

    if selection.numeric_features:
        numeric_pipeline = Pipeline(
            steps=[
                ("clean_infinite", FunctionTransformer(_replace_infinite_with_nan)),
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
            ]
        )
        transformers.append(("numeric", numeric_pipeline, selection.numeric_features))

    if selection.categorical_features:
        categorical_pipeline = Pipeline(
            steps=[
                ("impute", SimpleImputer(strategy="most_frequent")),
                ("encode", OneHotEncoder(handle_unknown="ignore")),
            ]
        )
        transformers.append(("categorical", categorical_pipeline, selection.categorical_features))

    return ColumnTransformer(transformers=transformers, remainder="drop")


def build_preprocessing_summary(selection: FeatureSelection) -> PreprocessingSummary:
    has_numeric = bool(selection.numeric_features)
    has_categorical = bool(selection.categorical_features)
    return PreprocessingSummary(
        numeric_features=selection.numeric_features,
        categorical_features=selection.categorical_features,
        numeric_transform=NUMERIC_TRANSFORM_DESCRIPTION if has_numeric else "n/a",
        categorical_transform=CATEGORICAL_TRANSFORM_DESCRIPTION if has_categorical else "n/a",
    )
