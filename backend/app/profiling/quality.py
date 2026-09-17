"""Deterministic data-quality checks.

Every finding is produced by a pure function of the dataset — no AI, no randomness, no
hard-coded per-dataset special-casing. Thresholds below are documented, fixed constants,
not learned or guessed; see `02_DOCS/decisions/DECISIONS_LOG.md` for the ADR recording
them. An empty `findings` list is a valid, correct result (a clean dataset), not an error.
"""

from datetime import UTC, datetime

import pandas as pd

from app.profiling.column_types import detect_semantic_type
from app.profiling.datetime_stats import compute_datetime_stats
from app.profiling.numeric_stats import compute_numeric_stats
from app.profiling.schemas import QualityFinding, QualitySeverity, QualitySummary, SemanticType

# Fixed, documented thresholds (not learned/guessed) — see ADR in DECISIONS_LOG.md.
_HIGH_MISSING_WARNING_THRESHOLD = 20.0
_HIGH_MISSING_CRITICAL_THRESHOLD = 50.0
_NEAR_CONSTANT_THRESHOLD = 0.95
_HIGH_CARDINALITY_CATEGORICAL_THRESHOLD = 0.5
_MIXED_TYPE_MIN_NUMERIC_RATIO = 0.10
_MIXED_TYPE_MAX_NUMERIC_RATIO = 0.90
_PRESUMED_NONNEGATIVE_KEYWORDS = ("age", "price", "amount", "quantity", "qty", "count", "total")


def _finding(
    code: str,
    severity: QualitySeverity,
    message: str,
    *,
    column: str | None = None,
    metric: float | int | None = None,
    details: dict | None = None,
) -> QualityFinding:
    return QualityFinding(
        code=code,
        severity=severity,
        column=column,
        message=message,
        metric=metric,
        details=details or {},
    )


def _dataset_level_findings(df: pd.DataFrame) -> list[QualityFinding]:
    findings: list[QualityFinding] = []
    row_count = len(df)
    column_count = len(df.columns)

    if column_count == 0:
        findings.append(
            _finding(
                "zero_columns",
                QualitySeverity.CRITICAL,
                "The dataset has no columns.",
            )
        )
        return findings  # nothing further can be evaluated

    if row_count == 0:
        findings.append(
            _finding(
                "empty_dataset",
                QualitySeverity.INFO,
                "The dataset has a header but zero data rows.",
            )
        )

    duplicate_row_count = int(df.duplicated().sum()) if row_count else 0
    if duplicate_row_count > 0:
        findings.append(
            _finding(
                "duplicate_rows",
                QualitySeverity.WARNING,
                f"{duplicate_row_count} duplicate row(s) found.",
                metric=duplicate_row_count,
                details={
                    "duplicate_row_percentage": round((duplicate_row_count / row_count) * 100, 4)
                },
            )
        )

    total_cells = row_count * column_count
    total_missing = int(df.isna().sum().sum()) if total_cells else 0
    if total_missing > 0:
        missing_pct = round((total_missing / total_cells) * 100, 4) if total_cells else 0.0
        severity = QualitySeverity.INFO
        if missing_pct >= _HIGH_MISSING_CRITICAL_THRESHOLD:
            severity = QualitySeverity.CRITICAL
        elif missing_pct >= _HIGH_MISSING_WARNING_THRESHOLD:
            severity = QualitySeverity.WARNING
        findings.append(
            _finding(
                "missing_values",
                severity,
                f"{total_missing} missing cell(s) across the dataset ({missing_pct}%).",
                metric=missing_pct,
            )
        )

    return findings


def _column_level_findings(series: pd.Series, row_count: int) -> list[QualityFinding]:
    findings: list[QualityFinding] = []
    name = str(series.name)
    non_null = series.dropna()
    non_null_count = len(non_null)

    if non_null_count == 0:
        # Nothing else below is meaningful for an entirely-empty column; the dataset-level
        # missing-values finding already covers it.
        return findings

    null_count = row_count - non_null_count
    null_pct = round((null_count / row_count) * 100, 4) if row_count else 0.0
    if null_pct >= _HIGH_MISSING_WARNING_THRESHOLD:
        severity = (
            QualitySeverity.CRITICAL
            if null_pct >= _HIGH_MISSING_CRITICAL_THRESHOLD
            else QualitySeverity.WARNING
        )
        findings.append(
            _finding(
                "column_high_missing",
                severity,
                f"Column '{name}' is {null_pct}% missing.",
                column=name,
                metric=null_pct,
            )
        )

    unique_count = non_null.nunique()
    if unique_count == 1:
        findings.append(
            _finding(
                "constant_column",
                QualitySeverity.WARNING,
                f"Column '{name}' has a single constant value across all non-null rows.",
                column=name,
                details={"value": str(non_null.iloc[0])},
            )
        )
    else:
        top_share = non_null.value_counts(normalize=True).iloc[0]
        if top_share >= _NEAR_CONSTANT_THRESHOLD:
            findings.append(
                _finding(
                    "near_constant_column",
                    QualitySeverity.INFO,
                    f"Column '{name}' is {round(top_share * 100, 2)}% a single value.",
                    column=name,
                    metric=round(float(top_share) * 100, 4),
                )
            )

    semantic_type = detect_semantic_type(series, row_count)

    if semantic_type == SemanticType.CATEGORICAL:
        unique_ratio = unique_count / non_null_count
        if unique_ratio > _HIGH_CARDINALITY_CATEGORICAL_THRESHOLD:
            findings.append(
                _finding(
                    "high_cardinality_categorical",
                    QualitySeverity.INFO,
                    f"Column '{name}' has unusually high cardinality for a categorical column "
                    f"({unique_count} distinct values across {non_null_count} rows).",
                    column=name,
                    metric=round(unique_ratio * 100, 4),
                )
            )

    if pd.api.types.is_object_dtype(series):
        numeric_ratio = pd.to_numeric(non_null, errors="coerce").notna().mean()
        if _MIXED_TYPE_MIN_NUMERIC_RATIO <= numeric_ratio <= _MIXED_TYPE_MAX_NUMERIC_RATIO:
            findings.append(
                _finding(
                    "mixed_type_column",
                    QualitySeverity.WARNING,
                    f"Column '{name}' appears to mix numeric and non-numeric values "
                    f"({round(numeric_ratio * 100, 2)}% numeric-looking).",
                    column=name,
                    metric=round(float(numeric_ratio) * 100, 4),
                )
            )

    if semantic_type == SemanticType.NUMERIC:
        stats = compute_numeric_stats(series)
        if stats.infinite_count > 0:
            findings.append(
                _finding(
                    "infinite_values",
                    QualitySeverity.CRITICAL,
                    f"Column '{name}' contains {stats.infinite_count} infinite value(s).",
                    column=name,
                    metric=stats.infinite_count,
                )
            )
        presumed_nonnegative = any(kw in name.lower() for kw in _PRESUMED_NONNEGATIVE_KEYWORDS)
        if stats.negative_count > 0 and presumed_nonnegative:
            findings.append(
                _finding(
                    "unexpected_negative_values",
                    QualitySeverity.WARNING,
                    f"Column '{name}' contains {stats.negative_count} negative value(s), "
                    "which is unusual for a column with this name.",
                    column=name,
                    metric=stats.negative_count,
                )
            )

    if semantic_type == SemanticType.DATETIME:
        dt_stats = compute_datetime_stats(series)
        if dt_stats.unparseable_count > 0:
            findings.append(
                _finding(
                    "invalid_datetime_values",
                    QualitySeverity.WARNING,
                    f"Column '{name}' has {dt_stats.unparseable_count} value(s) that could "
                    "not be parsed as dates.",
                    column=name,
                    metric=dt_stats.unparseable_count,
                )
            )

    return findings


def build_quality_summary(dataset_id: str, df: pd.DataFrame) -> QualitySummary:
    row_count = len(df)
    findings = _dataset_level_findings(df)

    if len(df.columns) > 0:
        for column in df.columns:
            findings.extend(_column_level_findings(df[column], row_count))

    return QualitySummary(
        dataset_id=dataset_id,
        findings=findings,
        finding_count=len(findings),
        generated_at=datetime.now(UTC),
    )
