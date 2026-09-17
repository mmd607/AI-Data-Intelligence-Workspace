"""Deterministic-first question routing.

Per `01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_PROMPT.md` section 11: "If a question can be
answered deterministically from existing structured data, prefer deterministic
computation/retrieval rather than asking the LLM to calculate it." This module recognizes
a fixed set of common question shapes and resolves them directly from Phase 02-04's own
computed output — the LLM (or the offline template renderer) only ever narrates an
already-resolved fact, it never computes the number itself.

This is intentionally a small, fixed set of patterns, not a natural-language-understanding
system — anything that doesn't match falls through to `EXPLANATION`/
`ANALYTICAL_INTERPRETATION` (handed to the provider with the full bounded context) or
`UNSUPPORTED` (the evidence genuinely can't help), per section 12: never guess.
"""

import re
from dataclasses import dataclass
from typing import Any

import pandas as pd

from app.ai.schemas import QuestionCategory
from app.profiling.column_profile import profile_column
from app.profiling.correlation import compute_correlation
from app.profiling.dataset_profile import build_dataset_profile
from app.profiling.schemas import SemanticType

_ML_METRIC_KEYWORDS = (
    "f1",
    "accuracy",
    "precision",
    "recall",
    "rmse",
    "r2",
    "r-squared",
    "mae",
    "mse",
)
_ML_PERFORMANCE_KEYWORDS = ("model perform", "baseline model", "how did the model")


@dataclass(frozen=True)
class RoutedQuestion:
    category: QuestionCategory
    resolved_answer: str | None


def route_question(
    question: str,
    df: pd.DataFrame,
    dataset_id: str,
    ml_result: dict[str, Any] | None,
) -> RoutedQuestion:
    q = question.lower()

    if "duplicate" in q:
        profile = build_dataset_profile(dataset_id, df)
        return RoutedQuestion(
            QuestionCategory.DETERMINISTIC_LOOKUP,
            f"{profile.duplicate_row_count} row(s) are exact duplicates "
            f"({profile.duplicate_row_percentage}% of {profile.row_count} total rows).",
        )

    if "missing" in q and any(word in q for word in ("most", "which", "highest")):
        profile = build_dataset_profile(dataset_id, df)
        if not profile.columns:
            return RoutedQuestion(QuestionCategory.UNSUPPORTED, None)
        worst = max(profile.columns, key=lambda c: c.null_percentage)
        return RoutedQuestion(
            QuestionCategory.DETERMINISTIC_LOOKUP,
            f"Column '{worst.name}' has the most missing values: {worst.null_percentage}% "
            f"({worst.null_count} of {profile.row_count} rows).",
        )

    if "correlat" in q and any(word in q for word in ("strong", "most", "which", "highest")):
        result = compute_correlation(dataset_id, df)
        if result.status == "insufficient_data" or not result.pairs:
            return RoutedQuestion(QuestionCategory.UNSUPPORTED, None)
        strongest = max(result.pairs, key=lambda p: abs(p.coefficient))
        return RoutedQuestion(
            QuestionCategory.DETERMINISTIC_LOOKUP,
            f"'{strongest.column_a}' and '{strongest.column_b}' have the strongest "
            f"computed correlation: {strongest.coefficient} (Pearson).",
        )

    stat_answer = _route_column_statistic_question(q, df)
    if stat_answer is not None:
        return RoutedQuestion(QuestionCategory.DETERMINISTIC_LOOKUP, stat_answer)

    is_ml_question = any(kw in q for kw in _ML_METRIC_KEYWORDS) or any(
        kw in q for kw in _ML_PERFORMANCE_KEYWORDS
    )
    if is_ml_question:
        if ml_result is None:
            return RoutedQuestion(QuestionCategory.UNSUPPORTED, None)
        metrics = ml_result.get("metrics", {})
        summary = ", ".join(f"{name}={value}" for name, value in metrics.items())
        return RoutedQuestion(
            QuestionCategory.DETERMINISTIC_LOOKUP,
            f"The {ml_result.get('model_name', 'baseline')} model reported: {summary}.",
        )

    if "quality" in q and ("issue" in q or "problem" in q):
        return RoutedQuestion(QuestionCategory.EXPLANATION, None)

    return RoutedQuestion(QuestionCategory.ANALYTICAL_INTERPRETATION, None)


def _route_column_statistic_question(q: str, df: pd.DataFrame) -> str | None:
    """Matches "what is the {mean|average|median|min|max|std} of {column}" style
    questions against real column names in the dataset."""
    stat_keywords = {
        "average": "mean",
        "mean": "mean",
        "median": "median",
        "minimum": "min",
        "min": "min",
        "maximum": "max",
        "max": "max",
        "standard deviation": "std",
    }
    matched_stat = next((key for key in stat_keywords if key in q), None)
    if matched_stat is None:
        return None

    # Word-boundary match, not a naive substring check — "age" must not match inside
    # "average" (a real bug caught by test_unknown_column_name_does_not_match).
    matched_column = next(
        (c for c in df.columns if re.search(rf"\b{re.escape(str(c).lower())}\b", q)),
        None,
    )
    if matched_column is None:
        return None

    profile = profile_column(df[matched_column], len(df))
    if profile.semantic_type != SemanticType.NUMERIC or profile.numeric_stats is None:
        return None

    stat_key = stat_keywords[matched_stat]
    value = getattr(profile.numeric_stats, stat_key)
    if value is None:
        return None
    return f"The {stat_key} of '{matched_column}' is {value}."
