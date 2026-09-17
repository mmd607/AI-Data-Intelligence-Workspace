"""API routers.

Per `02_DOCS/ARCHITECTURE.md` "Module Boundaries": routers here contain no business
logic — they validate input via Pydantic, call into the relevant service module
(ingestion / profiling / ml / ai, introduced in later phases), and shape the response.
"""
