"""Deterministic task-type suitability detection for a candidate target column.

Fixed, documented thresholds (see `02_DOCS/decisions/DECISIONS_LOG.md` ADR-012) — not
learned or guessed. Reuses Phase 03's `detect_semantic_type` rather than re-implementing
column-type inference, per `02_DOCS/ARCHITECTURE.md` "Profiling Architecture" ("Keep
profiling modular so future ML and AI layers can reuse computed information").
"""

import pandas as pd

from app.ml.schemas import ObservedTargetFacts, TaskSuitability, TaskType, ValidateTargetResponse
from app.profiling.column_types import detect_semantic_type
from app.profiling.schemas import SemanticType

MAX_MULTICLASS_CARDINALITY = 20
MIN_ROWS_FOR_TRAINING = 10


def evaluate_task_suitability(series: pd.Series, row_count: int) -> list[TaskSuitability]:
    """Evaluate every supported `TaskType` against this column's observed characteristics.

    `row_count` is the full dataset's row count (used only for `detect_semantic_type`,
    which needs it for its own text-vs-categorical cardinality ratio); the training-
    feasibility check below correctly uses the count of *non-null target values*, since
    rows with a missing target can never be used for supervised training regardless of
    how many rows the dataset has overall.

    A column may be suitable for more than one task type (e.g. an integer column with 4
    distinct values is a reasonable candidate for either multiclass classification or
    regression) — the caller decides, this function only reports what's structurally
    possible, never picks for them.
    """
    non_null = series.dropna()
    non_null_count = len(non_null)
    unique_count = int(non_null.nunique())
    semantic_type = detect_semantic_type(series, row_count)

    results: list[TaskSuitability] = []

    if non_null_count < MIN_ROWS_FOR_TRAINING:
        reason = (
            f"Only {non_null_count} non-null target value(s) available; at least "
            f"{MIN_ROWS_FOR_TRAINING} are required to train."
        )
        for task_type in TaskType:
            results.append(TaskSuitability(task_type=task_type, suitable=False, reason=reason))
        return results

    # Binary classification: exactly 2 distinct non-null values, any semantic type.
    if unique_count == 2:
        results.append(
            TaskSuitability(
                task_type=TaskType.BINARY_CLASSIFICATION,
                suitable=True,
                reason=f"Target has exactly 2 distinct values ({unique_count}).",
            )
        )
    else:
        results.append(
            TaskSuitability(
                task_type=TaskType.BINARY_CLASSIFICATION,
                suitable=False,
                reason=(
                    f"Binary classification requires exactly 2 distinct values; "
                    f"found {unique_count}."
                ),
            )
        )

    # Multiclass classification: 3..MAX_MULTICLASS_CARDINALITY distinct values.
    if 3 <= unique_count <= MAX_MULTICLASS_CARDINALITY:
        results.append(
            TaskSuitability(
                task_type=TaskType.MULTICLASS_CLASSIFICATION,
                suitable=True,
                reason=f"Target has {unique_count} distinct values (within the "
                f"3-{MAX_MULTICLASS_CARDINALITY} range treated as multiclass).",
            )
        )
    else:
        results.append(
            TaskSuitability(
                task_type=TaskType.MULTICLASS_CLASSIFICATION,
                suitable=False,
                reason=(
                    f"Multiclass classification requires 3-{MAX_MULTICLASS_CARDINALITY} "
                    f"distinct values; found {unique_count}."
                ),
            )
        )

    # Regression: semantic type must be numeric, and more than 2 distinct values (a
    # 2-valued numeric target is really binary classification in disguise — still
    # allowed, but only via the binary-classification path above).
    if semantic_type == SemanticType.NUMERIC and unique_count > 2:
        results.append(
            TaskSuitability(
                task_type=TaskType.REGRESSION,
                suitable=True,
                reason="Target is numeric with more than 2 distinct values.",
            )
        )
    else:
        reason = (
            "Regression requires a numeric target."
            if semantic_type != SemanticType.NUMERIC
            else "Target has only 2 distinct numeric values — use binary classification instead."
        )
        results.append(
            TaskSuitability(task_type=TaskType.REGRESSION, suitable=False, reason=reason)
        )

    return results


def suggest_task(suitabilities: list[TaskSuitability]) -> TaskType | None:
    """A conservative default suggestion — never a confirmed choice (see
    `ValidateTargetResponse.is_suggestion`, always `True`). Prefers classification over
    regression when both are structurally suitable, since a low-cardinality target is
    usually intended as a category even if it happens to be numeric.
    """
    by_type = {s.task_type: s for s in suitabilities}
    preference_order = (
        TaskType.BINARY_CLASSIFICATION,
        TaskType.MULTICLASS_CLASSIFICATION,
        TaskType.REGRESSION,
    )
    for task_type in preference_order:
        if by_type[task_type].suitable:
            return task_type
    return None


def build_validate_target_response(
    dataset_id: str, target_column: str, series: pd.Series, row_count: int
) -> ValidateTargetResponse:
    non_null = series.dropna()
    observed = ObservedTargetFacts(
        row_count=row_count,
        non_null_count=int(len(non_null)),
        null_count=int(row_count - len(non_null)),
        unique_count=int(non_null.nunique()),
        pandas_dtype=str(series.dtype),
        semantic_type=detect_semantic_type(series, row_count),
    )
    suitabilities = evaluate_task_suitability(series, row_count)
    return ValidateTargetResponse(
        dataset_id=dataset_id,
        target_column=target_column,
        observed=observed,
        suitable_tasks=suitabilities,
        suggested_task=suggest_task(suitabilities),
    )
