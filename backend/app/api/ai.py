"""AI analytics endpoints.

Thin router per `02_DOCS/ARCHITECTURE.md` "Module Boundaries" — all computation lives in
`app.ai`. Reuses Phase 02/03's dataset storage and loader, exactly like `app.api.ml`.
"""

from fastapi import APIRouter, Depends

from app.ai import service
from app.ai.factory import get_provider
from app.ai.provider import AIProvider
from app.ai.schemas import (
    AIAnalyzeRequest,
    AIAnalyzeResponse,
    AIQueryRequest,
    AIQueryResponse,
    AIStatusResponse,
)
from app.api.datasets import get_storage_service
from app.config import Settings, get_settings
from app.ingestion.storage import StorageService
from app.profiling.loader import load_dataframe

# Dataset-independent: not nested under /datasets/{dataset_id}.
status_router = APIRouter(prefix="/ai", tags=["ai"])


def get_ai_provider(settings: Settings = Depends(get_settings)) -> AIProvider | None:
    """A fresh provider instance per request, from current settings — overridable in
    tests via `app.dependency_overrides[get_ai_provider]` for a mocked provider.
    """
    return get_provider(settings)


@status_router.get("/status", response_model=AIStatusResponse)
def get_status(
    settings: Settings = Depends(get_settings),
    provider: AIProvider | None = Depends(get_ai_provider),
) -> AIStatusResponse:
    return service.get_status(provider, settings)


# Dataset-scoped AI operations.
router = APIRouter(prefix="/datasets/{dataset_id}/ai", tags=["ai"])


@router.post("/analyze", response_model=AIAnalyzeResponse)
def analyze(
    dataset_id: str,
    request: AIAnalyzeRequest,
    storage: StorageService = Depends(get_storage_service),
    provider: AIProvider | None = Depends(get_ai_provider),
) -> AIAnalyzeResponse:
    df = load_dataframe(dataset_id, storage)
    return service.analyze(dataset_id, df, request, provider)


@router.post("/query", response_model=AIQueryResponse)
def query(
    dataset_id: str,
    request: AIQueryRequest,
    storage: StorageService = Depends(get_storage_service),
    provider: AIProvider | None = Depends(get_ai_provider),
) -> AIQueryResponse:
    df = load_dataframe(dataset_id, storage)
    return service.query(dataset_id, df, request, provider)
