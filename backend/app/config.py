"""Application configuration.

All environment-specific values are read from environment variables (optionally via a
local `.env` file, never committed — see `.env.example`), never hardcoded, per
`02_DOCS/decisions/DECISIONS_LOG.md` and `00_AGENT_CONTROL/AGENT_MASTER_INSTRUCTIONS.md`
("Coding behavior").
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the backend service.

    Every field has a safe local-development default so the service starts with zero
    required configuration, per Phase 01's "Ensure local startup is documented" goal.
    """

    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    app_name: str = "AI Data Intelligence Workspace API"
    app_env: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    # Comma-separated list of allowed frontend origins for CORS during local development.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Dataset ingestion (Phase 02). Storage layout and these limits resolve the open
    # questions left in 02_DOCS/PRODUCT_SPEC.md and 02_DOCS/decisions/DECISIONS_LOG.md
    # ADR-005: filesystem + JSON sidecar per dataset, no database, for v1. Relative to the
    # backend process's working directory (i.e. `backend/data/uploads` when run the
    # documented way from `backend/`).
    data_dir: str = "data/uploads"
    max_upload_size_bytes: int = 50 * 1024 * 1024  # 50 MB — see ADR-005.

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — read once per process, per standard FastAPI practice."""
    return Settings()
