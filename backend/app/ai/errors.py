"""AI-specific errors — same `{code, message, status_code}` shape as
`IngestionError`/`ProfilingError`/`MLError`, kept independent per
`02_DOCS/ARCHITECTURE.md` "Module Boundaries".

Per section 19 of the phase prompt ("AI failures must never break deterministic
analytics"): an `AIError` is always caught at the API boundary and turned into a
structured, non-2xx-but-never-crashing response — it never propagates into or affects
`ingestion`/`profiling`/`ml`, which have no dependency on this module at all.
"""


class AIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)
