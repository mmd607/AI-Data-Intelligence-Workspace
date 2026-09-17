"""Deterministic, size-bounded evidence construction.

Every function here builds a plain dict from Phase 02-04's own already-computed output —
never from raw dataset rows, never estimating or inventing a value. The returned dict
(minus the internal `"_intent"` routing key) is used *both* as what's sent to the AI
provider *and* as the `computed` field returned to the API caller — so "what grounded this
response" and "what the provider saw" are provably the same object, never two different
things that could silently drift apart.

Size caps below are fixed, documented constants (matching the pattern established in
Phase 03/04 — see `02_DOCS/decisions/DECISIONS_LOG.md` ADR-014), applied so a wide dataset
never turns into an unbounded prompt (`01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_PROMPT.md`
section 20, "Cost / Token Control").
"""

from typing import Any

import pandas as pd

from app.ai.errors import AIError
from app.profiling.column_profile import profile_column
from app.profiling.correlation import compute_correlation
from app.profiling.dataset_profile import build_dataset_profile
from app.profiling.quality import build_quality_summary

MAX_SUMMARY_COLUMNS = 30
MAX_QUALITY_FINDINGS = 20
MAX_CORRELATION_PAIRS = 10

REQUIRED_ML_RESULT_FIELDS = (
    "task_type",
    "target_column",
    "model_name",
    "feature_columns",
    "train_size",
    "test_size_actual",
    "metrics",
)


def strip_intent(evidence: dict[str, Any]) -> dict[str, Any]:
    """Returns a copy of `evidence` without the internal `_intent` routing key — this is
    what's actually exposed to API callers as `computed`, never the raw dict with routing
    metadata mixed in.
    """
    return {k: v for k, v in evidence.items() if k != "_intent"}


def build_dataset_summary_evidence(dataset_id: str, df: pd.DataFrame) -> dict[str, Any]:
    profile = build_dataset_profile(dataset_id, df)
    quality = build_quality_summary(dataset_id, df)

    severity_counts: dict[str, int] = {}
    for finding in quality.findings:
        severity_counts[finding.severity.value] = severity_counts.get(finding.severity.value, 0) + 1

    columns = [
        {
            "name": c.name,
            "semantic_type": c.semantic_type.value,
            "null_percentage": c.null_percentage,
            "unique_percentage": c.unique_percentage,
        }
        for c in profile.columns[:MAX_SUMMARY_COLUMNS]
    ]

    return {
        "_intent": "dataset_summary",
        "dataset_id": dataset_id,
        "row_count": profile.row_count,
        "column_count": profile.column_count,
        "missing_percentage": profile.missing.missing_percentage,
        "duplicate_row_percentage": profile.duplicate_row_percentage,
        "quality_finding_count": quality.finding_count,
        "quality_severity_counts": severity_counts,
        "columns": columns,
    }


def build_quality_explanation_evidence(dataset_id: str, df: pd.DataFrame) -> dict[str, Any]:
    quality = build_quality_summary(dataset_id, df)
    findings = [
        {
            "code": f.code,
            "severity": f.severity.value,
            "column": f.column,
            "message": f.message,
            "metric": f.metric,
        }
        for f in quality.findings[:MAX_QUALITY_FINDINGS]
    ]
    return {
        "_intent": "quality_explanation",
        "dataset_id": dataset_id,
        "finding_count": quality.finding_count,
        "findings": findings,
    }


def build_column_insight_evidence(
    dataset_id: str, df: pd.DataFrame, column_name: str
) -> dict[str, Any]:
    if column_name not in df.columns:
        raise AIError(
            code="column_not_found",
            message=f"No column named '{column_name}' in dataset '{dataset_id}'.",
            status_code=404,
        )
    profile = profile_column(df[column_name], len(df))
    return {
        "_intent": "column_insight",
        "dataset_id": dataset_id,
        "column_name": profile.name,
        "pandas_dtype": profile.pandas_dtype,
        "semantic_type": profile.semantic_type.value,
        "null_count": profile.null_count,
        "null_percentage": profile.null_percentage,
        "unique_count": profile.unique_count,
        "unique_percentage": profile.unique_percentage,
        "sample_values": profile.sample_values,
        "numeric_stats": (profile.numeric_stats.model_dump() if profile.numeric_stats else None),
        "categorical_stats": (
            profile.categorical_stats.model_dump() if profile.categorical_stats else None
        ),
        "datetime_stats": (
            profile.datetime_stats.model_dump(mode="json") if profile.datetime_stats else None
        ),
    }


def build_correlation_explanation_evidence(dataset_id: str, df: pd.DataFrame) -> dict[str, Any]:
    result = compute_correlation(dataset_id, df)
    sorted_pairs = sorted(result.pairs, key=lambda p: abs(p.coefficient), reverse=True)
    pairs = [
        {
            "column_a": p.column_a,
            "column_b": p.column_b,
            "coefficient": p.coefficient,
            "observations": p.observations,
        }
        for p in sorted_pairs[:MAX_CORRELATION_PAIRS]
    ]
    return {
        "_intent": "correlation_explanation",
        "dataset_id": dataset_id,
        "method": result.method,
        "status": result.status,
        "message": result.message,
        "pairs": pairs,
    }


def build_ml_explanation_evidence(ml_result: dict[str, Any] | None) -> dict[str, Any]:
    if ml_result is None:
        raise AIError(
            code="ml_result_required",
            message="The 'ml_explanation' capability requires the caller to supply an "
            "'ml_result' (this module never re-runs training itself).",
            status_code=400,
        )
    missing = [f for f in REQUIRED_ML_RESULT_FIELDS if f not in ml_result]
    if missing:
        raise AIError(
            code="ml_result_malformed",
            message=f"The supplied 'ml_result' is missing required field(s): {missing}.",
            status_code=400,
        )
    return {
        "_intent": "ml_explanation",
        "task_type": ml_result["task_type"],
        "target_column": ml_result["target_column"],
        "model_name": ml_result["model_name"],
        "feature_columns": ml_result["feature_columns"],
        "train_size": ml_result["train_size"],
        "test_size_actual": ml_result["test_size_actual"],
        "metrics": ml_result["metrics"],
        "unavailable_metrics": ml_result.get("unavailable_metrics", {}),
        "warnings": ml_result.get("warnings", []),
        "limitations": ml_result.get("limitations", []),
    }
