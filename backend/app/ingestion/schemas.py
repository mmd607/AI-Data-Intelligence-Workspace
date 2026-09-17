"""Pydantic schemas for the ingestion API — the single source of truth for the
`/api/v1/datasets` response contract, per `02_DOCS/ARCHITECTURE.md` "API Contract
Philosophy".
"""

from datetime import datetime

from pydantic import BaseModel


class ColumnInfo(BaseModel):
    name: str
    dtype: str


class DatasetMetadata(BaseModel):
    """Full detail for one ingested dataset — returned by upload and get-by-id.

    Every field here is a structural fact produced deterministically while parsing the
    file (row_count, column_count, columns, missing_value_count, duplicate_row_count) —
    there is no `quality_score` or similar field; that is Phase 03's responsibility, built
    as its own module against this stored metadata, not added to it here.
    """

    id: str
    original_filename: str
    uploaded_at: datetime
    size_bytes: int
    row_count: int
    column_count: int
    columns: list[ColumnInfo]
    missing_value_count: int
    duplicate_row_count: int


class DatasetSummary(BaseModel):
    """Lighter shape for the list endpoint — no column-level detail."""

    id: str
    original_filename: str
    uploaded_at: datetime
    size_bytes: int
    row_count: int
    column_count: int


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
