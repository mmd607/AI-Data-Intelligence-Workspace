"""FastAPI application entrypoint.

App wiring, CORS, logging, structured error handling, and the versioned API mount point.
Phase 01 added the health endpoint; Phase 02 adds dataset ingestion. Profiling/ML/AI are
later phases' modules, mounted under `settings.api_prefix` as they're built.
"""

import logging

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import datasets, health
from app.config import get_settings
from app.ingestion.errors import IngestionError
from app.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)

# Versioned API surface, per `02_DOCS/ARCHITECTURE.md` "API Contract Philosophy". Profiling
# (Phase 03), ML (Phase 04), and AI (Phase 05) routers mount here in later phases.
api_v1 = APIRouter(prefix=settings.api_prefix)
api_v1.include_router(datasets.router)
app.include_router(api_v1)


@app.exception_handler(IngestionError)
async def ingestion_error_handler(request: Request, exc: IngestionError) -> JSONResponse:
    """Structured, correctly-statused response for client-caused ingestion failures —
    distinct from the catch-all 500 handler below, per
    `01_PHASES/PHASE_02_DATA_INGESTION/PHASE_PROMPT.md` ("clear errors for invalid
    files").
    """
    logger.info(
        "Ingestion error on %s %s: %s (%s)",
        request.method,
        request.url.path,
        exc.code,
        exc.message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Never leak internals; never fail silently.

    Per `00_AGENT_CONTROL/AGENT_MASTER_INSTRUCTIONS.md` ("Coding behavior" / "Error
    handling philosophy" in `02_DOCS/decisions/DECISIONS_LOG.md`-linked docs): every error
    returns a structured, non-leaking body, and is actually logged server-side.
    """
    logger.exception("Unhandled exception while processing %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred.",
            }
        },
    )
