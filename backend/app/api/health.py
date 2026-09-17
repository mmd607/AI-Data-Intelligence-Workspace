"""Health check endpoint.

Introduced in Phase 01 per `02_DOCS/decisions/DECISIONS_LOG.md` ADR-009 ("A backend health
endpoint is introduced as early as Phase 01"). Used by the frontend shell to display
backend connectivity status, and later by Docker Compose health checks (Phase 08).
"""

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    timestamp: datetime


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
        timestamp=datetime.now(UTC),
    )
