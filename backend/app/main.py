"""FastAPI application entrypoint.

Phase 01 scope only: app wiring, CORS, logging, structured error handling, and the health
endpoint. No product features (ingestion/profiling/ML/AI) live here yet — those are later
phases' modules, mounted under `settings.api_prefix` as they're built.
"""

import logging

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import health
from app.config import get_settings
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

# Versioned API surface for future phases (ingestion, profiling, ml, ai). Empty for now —
# Phase 02 mounts its own router here rather than at the app root, per
# `02_DOCS/ARCHITECTURE.md` "API Contract Philosophy".
api_v1 = APIRouter(prefix=settings.api_prefix)
app.include_router(api_v1)


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
