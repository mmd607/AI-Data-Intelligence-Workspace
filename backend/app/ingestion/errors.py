"""Ingestion-specific errors.

Raised by validation/parsing code and turned into a structured, non-leaking JSON body by
the handler registered in `app.main` — never a bare 500, per
`00_AGENT_CONTROL/AGENT_MASTER_INSTRUCTIONS.md` ("Error handling philosophy").
"""


class IngestionError(Exception):
    """A client-caused ingestion failure with a stable machine-readable `code`."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)
