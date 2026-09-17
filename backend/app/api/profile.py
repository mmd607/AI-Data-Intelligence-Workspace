"""Profiling endpoints.

Thin router per `02_DOCS/ARCHITECTURE.md` "Module Boundaries" — all computation lives in
`app.profiling`. Reuses Phase 02's dataset identification/storage mechanism
(`get_storage_service` from `app.api.datasets`) rather than introducing a second storage
system, per `01_PHASES/PHASE_03_DATA_PROFILING_VISUALIZATION/PHASE_PROMPT.md`.
"""

from fastapi import APIRouter, Depends

from app.api.datasets import get_storage_service
from app.ingestion.storage import StorageService
from app.profiling.column_profile import profile_column
from app.profiling.correlation import compute_correlation
from app.profiling.dataset_profile import build_dataset_profile
from app.profiling.distribution import compute_distributions
from app.profiling.errors import ProfilingError
from app.profiling.loader import load_dataframe
from app.profiling.quality import build_quality_summary
from app.profiling.schemas import (
    ColumnProfile,
    CorrelationResult,
    DatasetProfile,
    DistributionResult,
    QualitySummary,
)

router = APIRouter(prefix="/datasets/{dataset_id}", tags=["profiling"])


@router.get("/profile", response_model=DatasetProfile)
def get_dataset_profile(
    dataset_id: str,
    storage: StorageService = Depends(get_storage_service),
) -> DatasetProfile:
    df = load_dataframe(dataset_id, storage)
    return build_dataset_profile(dataset_id, df)


@router.get("/quality", response_model=QualitySummary)
def get_quality_summary(
    dataset_id: str,
    storage: StorageService = Depends(get_storage_service),
) -> QualitySummary:
    df = load_dataframe(dataset_id, storage)
    return build_quality_summary(dataset_id, df)


@router.get("/columns/{column_name}", response_model=ColumnProfile)
def get_column_profile(
    dataset_id: str,
    column_name: str,
    storage: StorageService = Depends(get_storage_service),
) -> ColumnProfile:
    df = load_dataframe(dataset_id, storage)
    if column_name not in df.columns:
        raise ProfilingError(
            code="column_not_found",
            message=f"No column named '{column_name}' in dataset '{dataset_id}'.",
            status_code=404,
        )
    return profile_column(df[column_name], len(df))


@router.get("/correlation", response_model=CorrelationResult)
def get_correlation(
    dataset_id: str,
    storage: StorageService = Depends(get_storage_service),
) -> CorrelationResult:
    df = load_dataframe(dataset_id, storage)
    return compute_correlation(dataset_id, df)


@router.get("/distribution", response_model=DistributionResult)
def get_distribution(
    dataset_id: str,
    storage: StorageService = Depends(get_storage_service),
) -> DistributionResult:
    df = load_dataframe(dataset_id, storage)
    return compute_distributions(dataset_id, df)
