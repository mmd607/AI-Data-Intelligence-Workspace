"""Training orchestration: ties validation, feature selection, splitting, preprocessing,
model fitting, and evaluation together into the structured `ModelResult` contract.

Leakage prevention is enforced by construction here: the train/test split happens once,
before any preprocessing is fit, and each model's `Pipeline` (preprocessing + estimator)
is fit only on the training split — `.predict(X_test)` reuses the already-fitted
preprocessing parameters, never refits on test data.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

import pandas as pd
from sklearn.pipeline import Pipeline

from app.ml.errors import MLError
from app.ml.evaluation import evaluate_classification, evaluate_regression
from app.ml.models import build_model
from app.ml.preprocessing import (
    FeatureSelection,
    build_preprocessing_summary,
    build_preprocessor,
    select_features,
)
from app.ml.schemas import ModelName, ModelResult, TaskType, TrainingConfig
from app.ml.splitting import split_dataset
from app.ml.target_validation import validate_target_for_training

SMALL_DATASET_WARNING_THRESHOLD = 50
HIGH_CARDINALITY_FEATURE_WARNING_THRESHOLD = 50


@dataclass
class PreparedTrainingData:
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    selection: FeatureSelection
    warnings: list[str]
    stratified: bool
    usable_row_count: int


def prepare_training_data(
    df: pd.DataFrame,
    target_column: str,
    task_type: TaskType,
    test_size: float,
    random_state: int,
) -> PreparedTrainingData:
    """Validate, select features, and split — shared by both single-model training and
    multi-model comparison, so every model in a comparison sees the identical split.
    """
    warnings = list(validate_target_for_training(df, target_column, task_type))

    # Rows with a missing target are unusable for supervised training — dropped here,
    # once, rather than at each downstream step.
    usable = df[df[target_column].notna()].reset_index(drop=True)

    selection = select_features(usable, target_column, len(usable))
    if not selection.feature_columns:
        raise MLError(
            code="no_usable_features",
            message="No usable feature columns remain after excluding the target and "
            "unsupported/constant columns.",
            status_code=400,
        )

    for column in selection.categorical_features:
        cardinality = int(usable[column].dropna().nunique())
        if cardinality > HIGH_CARDINALITY_FEATURE_WARNING_THRESHOLD:
            warnings.append(
                f"Feature '{column}' has high cardinality ({cardinality} distinct "
                "values) — one-hot encoding will produce many columns."
            )

    if len(usable) < SMALL_DATASET_WARNING_THRESHOLD:
        warnings.append(
            f"Only {len(usable)} usable rows — baseline metrics may be unstable at this scale."
        )

    X = usable[selection.feature_columns]
    y = usable[target_column]

    X_train, X_test, y_train, y_test = split_dataset(X, y, task_type, test_size, random_state)

    return PreparedTrainingData(
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        selection=selection,
        warnings=warnings,
        stratified=task_type != TaskType.REGRESSION,
        usable_row_count=len(usable),
    )


def train_single_model(
    prepared: PreparedTrainingData,
    dataset_id: str,
    target_column: str,
    task_type: TaskType,
    model_name: ModelName,
    test_size: float,
    random_state: int,
) -> ModelResult:
    preprocessor = build_preprocessor(prepared.selection)
    model = build_model(model_name, task_type, random_state)
    pipeline = Pipeline(steps=[("preprocess", preprocessor), ("model", model)])

    pipeline.fit(prepared.X_train, prepared.y_train)
    y_pred = pipeline.predict(prepared.X_test)

    limitations = [
        "Baseline model only — no hyperparameter tuning was performed.",
        "Free-text and datetime columns are excluded from features.",
    ]
    warnings = list(prepared.warnings)

    if task_type in (TaskType.BINARY_CLASSIFICATION, TaskType.MULTICLASS_CLASSIFICATION):
        y_proba = None
        if task_type == TaskType.BINARY_CLASSIFICATION and hasattr(pipeline, "predict_proba"):
            proba = pipeline.predict_proba(prepared.X_test)
            y_proba = proba[:, 1] if proba.shape[1] == 2 else None
        metrics, unavailable, confusion = evaluate_classification(
            prepared.y_test, y_pred, y_proba, task_type
        )
    else:
        metrics, unavailable = evaluate_regression(prepared.y_test, y_pred)
        confusion = None

    return ModelResult(
        dataset_id=dataset_id,
        target_column=target_column,
        task_type=task_type,
        feature_columns=prepared.selection.feature_columns,
        excluded_columns=prepared.selection.excluded_columns,
        preprocessing=build_preprocessing_summary(prepared.selection),
        model_name=model_name,
        training_config=TrainingConfig(
            test_size=test_size, random_state=random_state, stratified=prepared.stratified
        ),
        train_size=len(prepared.X_train),
        test_size_actual=len(prepared.X_test),
        metrics=metrics,
        unavailable_metrics=unavailable,
        confusion_matrix=confusion,
        warnings=warnings,
        limitations=limitations,
        generated_at=datetime.now(UTC),
    )
