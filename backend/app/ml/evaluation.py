"""Deterministic evaluation metrics.

Never computes a metric that is mathematically invalid for the task/data at hand — an
unavailable metric is reported by name with a reason in `unavailable_metrics`, never
silently omitted or replaced with a fabricated value.
"""

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)

from app.ml.schemas import ConfusionMatrixResult, TaskType


def evaluate_classification(
    y_true,
    y_pred,
    y_proba: np.ndarray | None,
    task_type: TaskType,
) -> tuple[dict[str, float], dict[str, str], ConfusionMatrixResult]:
    precision = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    recall = recall_score(y_true, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    metrics: dict[str, float] = {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 6),
        "precision": round(float(precision), 6),
        "recall": round(float(recall), 6),
        "f1": round(float(f1), 6),
    }
    unavailable: dict[str, str] = {}

    labels = sorted({*np.unique(y_true).tolist(), *np.unique(y_pred).tolist()}, key=str)
    matrix = confusion_matrix(y_true, y_pred, labels=labels).tolist()
    confusion = ConfusionMatrixResult(labels=[str(label) for label in labels], matrix=matrix)

    if task_type == TaskType.BINARY_CLASSIFICATION:
        if y_proba is not None and len(np.unique(y_true)) == 2:
            try:
                metrics["roc_auc"] = round(float(roc_auc_score(y_true, y_proba)), 6)
            except ValueError as exc:
                unavailable["roc_auc"] = f"Could not be computed: {exc}"
        else:
            unavailable["roc_auc"] = "Predicted probabilities were not available for this model."
    else:
        unavailable["roc_auc"] = "Not computed for multiclass baselines in this phase."

    return metrics, unavailable, confusion


def evaluate_regression(y_true, y_pred) -> tuple[dict[str, float], dict[str, str]]:
    metrics: dict[str, float] = {}
    unavailable: dict[str, str] = {}

    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    metrics["mae"] = round(float(mae), 6)
    metrics["mse"] = round(float(mse), 6)
    metrics["rmse"] = round(float(np.sqrt(mse)), 6)

    if len(y_true) < 2:
        unavailable["r2"] = "R² is undefined for a test set of fewer than 2 samples."
    else:
        metrics["r2"] = round(float(r2_score(y_true, y_pred)), 6)

    return metrics, unavailable
