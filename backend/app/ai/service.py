"""Orchestration: builds evidence, calls the configured provider, and assembles the
grounded response contract.

The core guarantee (`01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_PROMPT.md` section 22): the
`computed` field in every response is set from the evidence dict *before* the provider is
ever called, and is never touched afterward — whatever the provider returns as narrative
text has no path back into `computed`. A provider that "hallucinates" a different number
only affects `ai_explanation.text`; the response's `computed` value is provably unchanged.
See `tests/test_ai_grounding.py`.

AI failures are always caught here and turned into `available: false` with a `reason` —
`computed` is still returned. This module never raises for a provider failure; it only
raises `AIError` for a genuinely bad *request* (unknown column, malformed ml_result), which
the API layer turns into a structured 4xx, per `01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_PROMPT.md`
section 19 ("AI errors should be isolated and returned clearly").
"""

from datetime import UTC, datetime

import pandas as pd

from app.ai.errors import AIError
from app.ai.evidence import (
    build_column_insight_evidence,
    build_correlation_explanation_evidence,
    build_dataset_summary_evidence,
    build_ml_explanation_evidence,
    build_quality_explanation_evidence,
    strip_intent,
)
from app.ai.provider import AIProvider
from app.ai.routing import route_question
from app.ai.schemas import (
    AIAnalyzeRequest,
    AIAnalyzeResponse,
    AICapability,
    AIExplanation,
    AIQueryRequest,
    AIQueryResponse,
    AIStatusResponse,
    QuestionCategory,
)
from app.ai.security import SYSTEM_INSTRUCTIONS
from app.config import Settings

_CAPABILITY_EVIDENCE_SOURCES: dict[AICapability, list[str]] = {
    AICapability.DATASET_SUMMARY: ["dataset_metadata", "quality_report"],
    AICapability.QUALITY_EXPLANATION: ["quality_report"],
    AICapability.COLUMN_INSIGHT: ["column_statistics"],
    AICapability.CORRELATION_EXPLANATION: ["correlation_report"],
    AICapability.ML_EXPLANATION: ["ml_result"],
}

_CAPABILITY_LIMITATIONS: dict[AICapability, list[str]] = {
    AICapability.DATASET_SUMMARY: [
        "The dataset's domain/business purpose is not known and is not claimed.",
    ],
    AICapability.QUALITY_EXPLANATION: [
        "Whether a finding matters depends on intended use, which is not evidenced here.",
    ],
    AICapability.COLUMN_INSIGHT: [
        "The column's real-world meaning is inferred only from its name, never assumed.",
    ],
    AICapability.CORRELATION_EXPLANATION: [
        "Correlation does not imply causation.",
    ],
    AICapability.ML_EXPLANATION: [
        "Baseline metrics only — no claim of production-readiness is made.",
    ],
}


def get_status(provider: AIProvider | None, settings: Settings) -> AIStatusResponse:
    if provider is None:
        return AIStatusResponse(
            enabled=False,
            provider="disabled",
            model=None,
            available=False,
            reason="AI features are disabled.",
        )
    available, reason = provider.is_available()
    model = settings.ai_model if settings.ai_provider == "anthropic" else None
    return AIStatusResponse(
        enabled=True,
        provider=provider.name,
        model=model or None,
        available=available,
        reason=reason,
    )


def analyze(
    dataset_id: str,
    df: pd.DataFrame,
    request: AIAnalyzeRequest,
    provider: AIProvider | None,
) -> AIAnalyzeResponse:
    evidence = _build_analyze_evidence(dataset_id, df, request)
    computed = strip_intent(evidence)
    evidence_sources = _CAPABILITY_EVIDENCE_SOURCES[request.capability]
    limitations = list(_CAPABILITY_LIMITATIONS[request.capability])

    ai_explanation, available, reason = _generate(
        provider, evidence, user_request=f"Explain the {request.capability.value} for this dataset."
    )

    return AIAnalyzeResponse(
        dataset_id=dataset_id,
        capability=request.capability,
        computed=computed,
        evidence_sources=evidence_sources,
        ai_explanation=ai_explanation,
        grounded=True,  # every response here is built from real, already-computed evidence
        limitations=limitations,
        available=available,
        reason=reason,
    )


def query(
    dataset_id: str,
    df: pd.DataFrame,
    request: AIQueryRequest,
    provider: AIProvider | None,
) -> AIQueryResponse:
    routed = route_question(request.question, df, dataset_id, request.ml_result)

    evidence: dict = {
        "_intent": "query",
        "dataset_id": dataset_id,
        "question": request.question,
        "question_category": routed.category.value,
        "resolved_answer": routed.resolved_answer,
    }
    if routed.category in (
        QuestionCategory.EXPLANATION,
        QuestionCategory.ANALYTICAL_INTERPRETATION,
    ):
        evidence["context"] = strip_intent(build_dataset_summary_evidence(dataset_id, df))

    computed = strip_intent(evidence)
    limitations = [
        "Only questions matching a recognized evidence-backed pattern are answered "
        "precisely; free-form interpretation is clearly separated from fact.",
    ]
    if routed.category == QuestionCategory.UNSUPPORTED:
        limitations.append("The available dataset evidence does not support this question.")

    ai_explanation, available, reason = _generate(provider, evidence, user_request=request.question)

    return AIQueryResponse(
        dataset_id=dataset_id,
        question=request.question,
        question_category=routed.category,
        computed=computed,
        evidence_sources=["dataset_metadata", "quality_report", "correlation_report"],
        ai_explanation=ai_explanation,
        grounded=True,
        limitations=limitations,
        available=available,
        reason=reason,
    )


def _build_analyze_evidence(dataset_id: str, df: pd.DataFrame, request: AIAnalyzeRequest) -> dict:
    if request.capability == AICapability.DATASET_SUMMARY:
        return build_dataset_summary_evidence(dataset_id, df)
    if request.capability == AICapability.QUALITY_EXPLANATION:
        return build_quality_explanation_evidence(dataset_id, df)
    if request.capability == AICapability.COLUMN_INSIGHT:
        if not request.column_name:
            raise AIError(
                code="column_name_required",
                message="The 'column_insight' capability requires 'column_name'.",
                status_code=400,
            )
        return build_column_insight_evidence(dataset_id, df, request.column_name)
    if request.capability == AICapability.CORRELATION_EXPLANATION:
        return build_correlation_explanation_evidence(dataset_id, df)
    if request.capability == AICapability.ML_EXPLANATION:
        return build_ml_explanation_evidence(request.ml_result)
    # Unreachable in practice: `request.capability` is a Pydantic-validated `AICapability`
    # enum member, and every current member is handled above — this only guards against a
    # future enum addition here being forgotten, per the project's documented-exception
    # policy for provably-unreachable defensive code (`02_DOCS/TESTING_STRATEGY.md`).
    raise AIError(  # pragma: no cover
        code="unsupported_capability", message=f"Unknown capability '{request.capability}'."
    )


def _generate(
    provider: AIProvider | None, evidence: dict, user_request: str
) -> tuple[AIExplanation | None, bool, str | None]:
    if provider is None:
        return None, False, "AI features are disabled."

    available, reason = provider.is_available()
    if not available:
        return None, False, reason

    try:
        result = provider.generate(SYSTEM_INSTRUCTIONS, evidence, user_request)
    except AIError as exc:
        return None, False, exc.message

    explanation = AIExplanation(
        provider=result.provider,
        model=result.model,
        text=result.text,
        generated_at=datetime.now(UTC),
    )
    return explanation, True, None
