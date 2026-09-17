"""Deterministic train/test splitting.

Stratification is applied automatically for classification tasks (already validated by
`target_validation.py` to have enough samples per class to support it). The random seed
is always the caller-supplied `random_state`, recorded verbatim in the result — never a
hidden or re-randomized value.
"""

import pandas as pd
from sklearn.model_selection import train_test_split

from app.ml.errors import MLError
from app.ml.schemas import TaskType


def split_dataset(
    X: pd.DataFrame,  # noqa: N803 - conventional ML naming
    y: pd.Series,
    task_type: TaskType,
    test_size: float,
    random_state: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    row_count = len(X)
    expected_test_count = row_count * test_size
    expected_train_count = row_count * (1 - test_size)

    if not (0.0 < test_size < 1.0):
        raise MLError(
            code="invalid_split_configuration",
            message=f"test_size must be strictly between 0 and 1; got {test_size}.",
            status_code=400,
        )

    if expected_test_count < 1 or expected_train_count < 1:
        raise MLError(
            code="invalid_split_configuration",
            message=(
                f"test_size={test_size} on {row_count} rows would leave an empty train or "
                "test split."
            ),
            status_code=400,
        )

    classification_tasks = (TaskType.BINARY_CLASSIFICATION, TaskType.MULTICLASS_CLASSIFICATION)
    stratify = y if task_type in classification_tasks else None

    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )
