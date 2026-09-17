"""Deterministic target-column validation.

Every check either passes silently, raises a structured `MLError` with a specific,
machine-readable `code` (never a bare 500), or contributes a non-fatal entry to the
returned warnings list. Nothing here ever silently substitutes a different target or task
type — per the phase prompt's "Target Handling": "Never silently choose an arbitrary
target when explicit target selection is required by the API."
"""

import pandas as pd

from app.ml.errors import MLError
from app.ml.schemas import TaskType
from app.ml.task_detection import MAX_MULTICLASS_CARDINALITY, MIN_ROWS_FOR_TRAINING
from app.profiling.column_types import detect_semantic_type
from app.profiling.schemas import SemanticType

MIN_SAMPLES_PER_CLASS = 2
MINORITY_CLASS_WARNING_SHARE = 0.05


def validate_target_for_training(
    df: pd.DataFrame, target_column: str, task_type: TaskType
) -> list[str]:
    """Validate a target column against a requested task type.

    Returns a (possibly empty) list of non-fatal warnings. Raises `MLError` for anything
    that must block training outright.
    """
    if target_column not in df.columns:
        raise MLError(
            code="target_not_found",
            message=f"No column named '{target_column}' in this dataset.",
            status_code=404,
        )

    series = df[target_column]
    non_null = series.dropna()

    if non_null.empty:
        raise MLError(
            code="target_all_missing",
            message=f"Target column '{target_column}' has no non-null values.",
            status_code=400,
        )

    # Rows with a missing target can never be used for supervised training, regardless
    # of the dataset's total row count — the feasibility check uses the non-null count.
    non_null_count = len(non_null)
    if non_null_count < MIN_ROWS_FOR_TRAINING:
        raise MLError(
            code="insufficient_rows",
            message=(
                f"Target column '{target_column}' has only {non_null_count} non-null "
                f"value(s); at least {MIN_ROWS_FOR_TRAINING} are required to train."
            ),
            status_code=400,
        )

    unique_count = int(non_null.nunique())
    classification_tasks = (TaskType.BINARY_CLASSIFICATION, TaskType.MULTICLASS_CLASSIFICATION)

    if task_type in classification_tasks and unique_count == 1:
        raise MLError(
            code="single_class_target",
            message=f"Target column '{target_column}' has only a single distinct value; "
            "a classifier cannot be trained on one class.",
            status_code=400,
        )

    warnings: list[str] = []

    if task_type == TaskType.BINARY_CLASSIFICATION:
        if unique_count != 2:
            raise MLError(
                code="invalid_target_cardinality",
                message=f"Binary classification requires exactly 2 distinct values; "
                f"'{target_column}' has {unique_count}.",
                status_code=400,
            )
        warnings.extend(_classification_class_checks(non_null, target_column))

    elif task_type == TaskType.MULTICLASS_CLASSIFICATION:
        if not (3 <= unique_count <= MAX_MULTICLASS_CARDINALITY):
            raise MLError(
                code="invalid_target_cardinality",
                message=(
                    f"Multiclass classification requires 3-{MAX_MULTICLASS_CARDINALITY} "
                    f"distinct values; '{target_column}' has {unique_count}."
                ),
                status_code=400,
            )
        warnings.extend(_classification_class_checks(non_null, target_column))

    elif task_type == TaskType.REGRESSION:
        semantic_type = detect_semantic_type(series, len(series))
        if semantic_type != SemanticType.NUMERIC:
            raise MLError(
                code="target_type_incompatible",
                message=f"Regression requires a numeric target; '{target_column}' was "
                f"classified as {semantic_type.value}.",
                status_code=400,
            )
        if unique_count <= 2:
            warnings.append(
                f"Target '{target_column}' has only {unique_count} distinct numeric "
                "value(s) — consider binary classification instead."
            )

    return warnings


def _classification_class_checks(non_null: pd.Series, target_column: str) -> list[str]:
    warnings: list[str] = []
    value_counts = non_null.value_counts()

    smallest_class_count = int(value_counts.min())
    if smallest_class_count < MIN_SAMPLES_PER_CLASS:
        raise MLError(
            code="insufficient_class_samples",
            message=(
                f"Target column '{target_column}' has a class with only "
                f"{smallest_class_count} sample(s); at least {MIN_SAMPLES_PER_CLASS} are "
                "required per class for a train/test split."
            ),
            status_code=400,
        )

    smallest_class_share = float(value_counts.min() / value_counts.sum())
    if smallest_class_share < MINORITY_CLASS_WARNING_SHARE:
        warnings.append(
            f"Target '{target_column}' is highly imbalanced — the smallest class is only "
            f"{round(smallest_class_share * 100, 2)}% of observations. Metrics (especially "
            "accuracy) should be interpreted with caution."
        )

    return warnings
