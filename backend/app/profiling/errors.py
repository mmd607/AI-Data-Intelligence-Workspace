"""Profiling-specific errors — same shape as `app.ingestion.errors.IngestionError`
(stable `code` + HTTP status), kept as an independent class per
`02_DOCS/ARCHITECTURE.md` "Module Boundaries" (profiling does not depend on ingestion's
error type, even though the JSON envelope they produce is identical).
"""


class ProfilingError(Exception):
    """A client-caused or data-caused profiling failure with a stable, machine-readable
    `code`. Never a bare 500 for an expected condition (missing dataset, empty dataset,
    unreadable file, etc.) — see `app.main`'s exception handler.
    """

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)
