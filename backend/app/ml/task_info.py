"""Static, dataset-independent information about supported ML task types — backs the
"inspect available ML task types" API operation.
"""

from app.ml.models import supported_models
from app.ml.schemas import TaskType, TaskTypeInfo, TaskTypesResponse

_DESCRIPTIONS: dict[TaskType, tuple[str, str]] = {
    TaskType.BINARY_CLASSIFICATION: (
        "Binary Classification",
        "Predicts one of exactly two classes. Requires a target column with exactly 2 "
        "distinct values.",
    ),
    TaskType.MULTICLASS_CLASSIFICATION: (
        "Multiclass Classification",
        "Predicts one of several discrete classes. Requires a target column with 3-20 "
        "distinct values.",
    ),
    TaskType.REGRESSION: (
        "Regression",
        "Predicts a continuous numeric value. Requires a numeric target column with "
        "more than 2 distinct values.",
    ),
}


def get_task_types_response() -> TaskTypesResponse:
    return TaskTypesResponse(
        task_types=[
            TaskTypeInfo(
                task_type=task_type,
                label=label,
                description=description,
                supported_models=supported_models(task_type),
            )
            for task_type, (label, description) in _DESCRIPTIONS.items()
        ]
    )
