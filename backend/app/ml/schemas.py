"""Pydantic schemas for the ML API.

Per this phase's Core Principle, every result explicitly separates: observed dataset
facts, inferred/requested task type, selected features, preprocessing, model, metrics,
warnings, and limitations — never one opaque blob. Nothing here contains AI-generated
text; Phase 05 explains these already-computed results, it never extends this contract.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.profiling.schemas import SemanticType


class TaskType(str, Enum):
    BINARY_CLASSIFICATION = "binary_classification"
    MULTICLASS_CLASSIFICATION = "multiclass_classification"
    REGRESSION = "regression"


class ModelName(str, Enum):
    LOGISTIC_REGRESSION = "logistic_regression"
    RANDOM_FOREST_CLASSIFIER = "random_forest_classifier"
    LINEAR_REGRESSION = "linear_regression"
    RIDGE_REGRESSION = "ridge_regression"
    RANDOM_FOREST_REGRESSOR = "random_forest_regressor"


# ---------------------------------------------------------------------------
# Static task-type inspection
# ---------------------------------------------------------------------------


class TaskTypeInfo(BaseModel):
    task_type: TaskType
    label: str
    description: str
    supported_models: list[ModelName]


class TaskTypesResponse(BaseModel):
    task_types: list[TaskTypeInfo]


# ---------------------------------------------------------------------------
# Target validation / suitability
# ---------------------------------------------------------------------------


class ObservedTargetFacts(BaseModel):
    """Observed dataset facts — never inferred, never a task-type opinion."""

    row_count: int
    non_null_count: int
    null_count: int
    unique_count: int
    pandas_dtype: str
    semantic_type: SemanticType


class TaskSuitability(BaseModel):
    task_type: TaskType
    suitable: bool
    reason: str


class ValidateTargetRequest(BaseModel):
    target_column: str


class ValidateTargetResponse(BaseModel):
    dataset_id: str
    target_column: str
    observed: ObservedTargetFacts
    suitable_tasks: list[TaskSuitability]
    suggested_task: TaskType | None
    is_suggestion: bool = True
    """Always true — this endpoint never trains anything or commits to a task type on the
    caller's behalf; see `01_PHASES/PHASE_04_ML_ENGINE/PHASE_PROMPT.md` "Target Handling":
    "If automatic target suggestion is implemented, clearly label it as a suggestion."
    """


# ---------------------------------------------------------------------------
# Training / comparison requests
# ---------------------------------------------------------------------------


class TrainRequest(BaseModel):
    """Both `target_column` and `task_type` are required and explicit — never an
    arbitrary auto-selected target, per the phase prompt's "Target Handling" requirement.
    """

    # `model_name` collides with Pydantic's reserved `model_` attribute prefix
    # (protected_namespaces) — it's still the correct field name for our domain, so the
    # protection is disabled here rather than renaming the field.
    model_config = ConfigDict(protected_namespaces=())

    target_column: str
    task_type: TaskType
    model_name: ModelName
    test_size: float = 0.2
    random_state: int = 42


class CompareRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    target_column: str
    task_type: TaskType
    model_names: list[ModelName]
    test_size: float = 0.2
    random_state: int = 42


# ---------------------------------------------------------------------------
# Result contract
# ---------------------------------------------------------------------------


class ExcludedColumn(BaseModel):
    column: str
    reason: str


class PreprocessingSummary(BaseModel):
    numeric_features: list[str]
    categorical_features: list[str]
    numeric_transform: str
    categorical_transform: str


class TrainingConfig(BaseModel):
    test_size: float
    random_state: int
    stratified: bool


class ConfusionMatrixResult(BaseModel):
    labels: list[str]
    matrix: list[list[int]]


class ModelResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    dataset_id: str
    target_column: str
    task_type: TaskType
    feature_columns: list[str]
    excluded_columns: list[ExcludedColumn]
    preprocessing: PreprocessingSummary
    model_name: ModelName
    training_config: TrainingConfig
    train_size: int
    test_size_actual: int
    metrics: dict[str, float]
    unavailable_metrics: dict[str, str]
    """Metric name -> reason it could not be computed — never silently absent with no
    explanation (e.g. `{"roc_auc": "not computed for multiclass baseline in this phase"}`).
    """
    confusion_matrix: ConfusionMatrixResult | None
    warnings: list[str]
    limitations: list[str]
    generated_at: datetime


class ComparisonResult(BaseModel):
    dataset_id: str
    target_column: str
    task_type: TaskType
    results: list[ModelResult]
    """One full `ModelResult` per requested model, all trained on the identical
    train/test split and preprocessing rules. No aggregate "AI score" or automatic winner
    field — per `01_PHASES/PHASE_04_ML_ENGINE/PHASE_PROMPT.md` "Model Comparison", that
    judgment is left to a future UI/AI layer, explaining the trade-offs from these
    structured numbers.
    """
    generated_at: datetime
