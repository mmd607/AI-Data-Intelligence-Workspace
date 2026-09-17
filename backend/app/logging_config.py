"""Basic structured-enough logging setup for the backend service.

Kept deliberately simple in Phase 01 — just enough to give every request/error a
timestamped, leveled log line. Later phases may replace this with structured JSON logging
if a real production need for it appears (documented in
`02_DOCS/decisions/DECISIONS_LOG.md` when it does).
"""

import logging

from app.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
