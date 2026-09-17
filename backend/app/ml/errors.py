"""ML-specific errors — same `{code, message, status_code}` shape as
`IngestionError`/`ProfilingError`, kept independent per
`02_DOCS/ARCHITECTURE.md` "Module Boundaries".
"""


class MLError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)
