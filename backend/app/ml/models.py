"""A small, fixed baseline model registry — deliberately not a "model zoo."

Per `01_PHASES/PHASE_04_ML_ENGINE/PHASE_PROMPT.md`: "Do not add a huge model zoo." XGBoost
was concretely evaluated for this phase and not adopted — see
`02_DOCS/decisions/DECISIONS_LOG.md` ADR-012.
"""

from collections.abc import Callable

from sklearn.base import BaseEstimator
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge

from app.ml.errors import MLError
from app.ml.schemas import ModelName, TaskType

_N_ESTIMATORS = 100

CLASSIFICATION_MODELS: dict[ModelName, Callable[[int], BaseEstimator]] = {
    ModelName.LOGISTIC_REGRESSION: lambda random_state: LogisticRegression(
        max_iter=1000, random_state=random_state
    ),
    ModelName.RANDOM_FOREST_CLASSIFIER: lambda random_state: RandomForestClassifier(
        n_estimators=_N_ESTIMATORS, random_state=random_state
    ),
}

REGRESSION_MODELS: dict[ModelName, Callable[[int], BaseEstimator]] = {
    ModelName.LINEAR_REGRESSION: lambda random_state: LinearRegression(),
    ModelName.RIDGE_REGRESSION: lambda random_state: Ridge(random_state=random_state),
    ModelName.RANDOM_FOREST_REGRESSOR: lambda random_state: RandomForestRegressor(
        n_estimators=_N_ESTIMATORS, random_state=random_state
    ),
}

MODELS_BY_TASK: dict[TaskType, dict[ModelName, Callable[[int], BaseEstimator]]] = {
    TaskType.BINARY_CLASSIFICATION: CLASSIFICATION_MODELS,
    TaskType.MULTICLASS_CLASSIFICATION: CLASSIFICATION_MODELS,
    TaskType.REGRESSION: REGRESSION_MODELS,
}


def supported_models(task_type: TaskType) -> list[ModelName]:
    return list(MODELS_BY_TASK[task_type].keys())


def build_model(model_name: ModelName, task_type: TaskType, random_state: int) -> BaseEstimator:
    models = MODELS_BY_TASK[task_type]
    if model_name not in models:
        raise MLError(
            code="invalid_model_for_task",
            message=(
                f"Model '{model_name.value}' is not available for task "
                f"'{task_type.value}'. Supported models: "
                f"{[m.value for m in models]}."
            ),
            status_code=400,
        )
    return models[model_name](random_state)
