"""Model comparison: multiple baseline models evaluated under one identical
train/test split and preprocessing ruleset, per
`01_PHASES/PHASE_04_ML_ENGINE/PHASE_PROMPT.md` "Model Comparison".

Deliberately produces no aggregate score and declares no automatic winner — each model's
full `ModelResult` is returned as-is, for a future layer to compare.
"""

from datetime import UTC, datetime

import pandas as pd

from app.ml.schemas import ComparisonResult, ModelName, TaskType
from app.ml.training import prepare_training_data, train_single_model


def compare_models(
    df: pd.DataFrame,
    dataset_id: str,
    target_column: str,
    task_type: TaskType,
    model_names: list[ModelName],
    test_size: float,
    random_state: int,
) -> ComparisonResult:
    prepared = prepare_training_data(df, target_column, task_type, test_size, random_state)

    results = [
        train_single_model(
            prepared=prepared,
            dataset_id=dataset_id,
            target_column=target_column,
            task_type=task_type,
            model_name=model_name,
            test_size=test_size,
            random_state=random_state,
        )
        for model_name in model_names
    ]

    return ComparisonResult(
        dataset_id=dataset_id,
        target_column=target_column,
        task_type=task_type,
        results=results,
        generated_at=datetime.now(UTC),
    )
