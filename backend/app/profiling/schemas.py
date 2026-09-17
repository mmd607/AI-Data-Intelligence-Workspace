"""Pydantic schemas for the profiling API.

Every field is a computed fact (`02_DOCS/ARCHITECTURE.md` "Data Flow" — the
computed/AI-generated envelope this whole project is built around). Nothing here is a
narrative or an AI-generated field; Phase 05 wraps these payloads for the AI layer, it
never extends them.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class SemanticType(str, Enum):
    NUMERIC = "numeric"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    CATEGORICAL = "categorical"
    TEXT = "text"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Column-level statistics, one block per semantic type. Exactly one of
# numeric_stats/categorical_stats/datetime_stats is populated on a given
# ColumnProfile, matching its semantic_type (boolean/unknown columns get none of the
# three — their null/unique counts on ColumnProfile itself are all that applies).
# ---------------------------------------------------------------------------


class NumericColumnStats(BaseModel):
    min: float | None
    max: float | None
    mean: float | None
    median: float | None
    std: float | None
    q1: float | None
    q3: float | None
    iqr: float | None
    zero_count: int
    negative_count: int
    infinite_count: int


class ValueFrequency(BaseModel):
    value: str
    count: int
    percentage: float


class CategoricalColumnStats(BaseModel):
    cardinality: int
    top_values: list[ValueFrequency]
    rare_value_count: int
    """Number of distinct values that occur exactly once (a conservative, deterministic
    definition of "rare" — see `01_PHASES/PHASE_03_DATA_PROFILING_VISUALIZATION/PHASE_PROMPT.md`
    "rare-value information where useful")."""


class DatetimeColumnStats(BaseModel):
    min_date: datetime | None
    max_date: datetime | None
    date_range_days: float | None
    missing_count: int
    unparseable_count: int


class ColumnProfile(BaseModel):
    name: str
    pandas_dtype: str
    semantic_type: SemanticType
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    sample_values: list[Any]
    numeric_stats: NumericColumnStats | None = None
    categorical_stats: CategoricalColumnStats | None = None
    datetime_stats: DatetimeColumnStats | None = None


class MissingValueSummary(BaseModel):
    total_missing_cells: int
    missing_percentage: float
    columns_with_missing: int


class DatasetProfile(BaseModel):
    dataset_id: str
    row_count: int
    column_count: int
    memory_usage_bytes: int
    duplicate_row_count: int
    duplicate_row_percentage: float
    missing: MissingValueSummary
    columns: list[ColumnProfile]
    generated_at: datetime


# ---------------------------------------------------------------------------
# Data quality findings
# ---------------------------------------------------------------------------


class QualitySeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class QualityFinding(BaseModel):
    code: str
    severity: QualitySeverity
    column: str | None
    message: str
    metric: float | int | None
    details: dict[str, Any]


class QualitySummary(BaseModel):
    dataset_id: str
    findings: list[QualityFinding]
    finding_count: int
    generated_at: datetime


# ---------------------------------------------------------------------------
# Correlation
# ---------------------------------------------------------------------------


class CorrelationPair(BaseModel):
    column_a: str
    column_b: str
    coefficient: float
    observations: int


class CorrelationResult(BaseModel):
    dataset_id: str
    method: str
    minimum_observations: int
    eligible_columns: list[str]
    pairs: list[CorrelationPair]
    status: str
    """`"computed"` or `"insufficient_data"` — never silently empty with no explanation."""
    message: str | None
    generated_at: datetime


# ---------------------------------------------------------------------------
# Distribution / histogram
# ---------------------------------------------------------------------------


class HistogramBin(BaseModel):
    bin_start: float
    bin_end: float
    count: int


class ColumnDistribution(BaseModel):
    column: str
    bin_count: int
    bins: list[HistogramBin]
    min: float
    max: float


class DistributionResult(BaseModel):
    dataset_id: str
    columns: list[ColumnDistribution]
    skipped_columns: list[str]
    generated_at: datetime
