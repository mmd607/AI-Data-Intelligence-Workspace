"""ML endpoints.

Thin router per `02_DOCS/ARCHITECTURE.md` "Module Boundaries" — all computation lives in
`app.ml`. Reuses Phase 02/03's dataset storage and loader rather than a second storage
system, per `01_PHASES/PHASE_04_ML_ENGINE/PHASE_PROMPT.md`.
"""

from fastapi import APIRouter, Depends

from app.api.datasets import get_storage_service
from app.ingestion.storage import StorageService
from app.ml.comparison import compare_models
from app.ml.errors import MLError
from app.ml.schemas import (
    CompareRequest,
    ComparisonResult,
    ModelResult,
    TaskTypesResponse,
    TrainRequest,
    ValidateTargetRequest,
    ValidateTargetResponse,
)
from app.ml.task_detection import build_validate_target_response
from app.ml.task_info import get_task_types_response
from app.ml.training import prepare_training_data, train_single_model
from app.profiling.loader import load_dataframe

# Dataset-independent: not nested under /datasets/{dataset_id}.
task_types_router = APIRouter(prefix="/ml", tags=["ml"])


@task_types_router.get("/task-types", response_model=TaskTypesResponse)
def get_task_types() -> TaskTypesResponse:
    return get_task_types_response()


# Dataset-scoped ML operations.
router = APIRouter(prefix="/datasets/{dataset_id}/ml", tags=["ml"])


@router.post("/validate-target", response_model=ValidateTargetResponse)
def validate_target(
    dataset_id: str,
    request: ValidateTargetRequest,
    storage: StorageService = Depends(get_storage_service),
) -> ValidateTargetResponse:
    df = load_dataframe(dataset_id, storage)
    if request.target_column not in df.columns:
        raise MLError(
            code="target_not_found",
            message=f"No column named '{request.target_column}' in dataset '{dataset_id}'.",
            status_code=404,
        )
    return build_validate_target_response(
        dataset_id, request.target_column, df[request.target_column], len(df)
    )


@router.post("/train", response_model=ModelResult)
def train(
    dataset_id: str,
    request: TrainRequest,
    storage: StorageService = Depends(get_storage_service),
) -> ModelResult:
    df = load_dataframe(dataset_id, storage)
    prepared = prepare_training_data(
        df, request.target_column, request.task_type, request.test_size, request.random_state
    )
    return train_single_model(
        prepared=prepared,
        dataset_id=dataset_id,
        target_column=request.target_column,
        task_type=request.task_type,
        model_name=request.model_name,
        test_size=request.test_size,
        random_state=request.random_state,
    )


@router.post("/compare", response_model=ComparisonResult)
def compare(
    dataset_id: str,
    request: CompareRequest,
    storage: StorageService = Depends(get_storage_service),
) -> ComparisonResult:
    df = load_dataframe(dataset_id, storage)
    return compare_models(
        df=df,
        dataset_id=dataset_id,
        target_column=request.target_column,
        task_type=request.task_type,
        model_names=request.model_names,
        test_size=request.test_size,
        random_state=request.random_state,
    )
