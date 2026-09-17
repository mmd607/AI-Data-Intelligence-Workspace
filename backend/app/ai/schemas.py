"""Pydantic schemas for the AI analytics API.

Follows the computed/AI-generated envelope already documented in
`02_DOCS/ARCHITECTURE.md` "Data Flow & the Computed/AI-Generated Contract": `computed`
holds the exact deterministic evidence (verbatim — this *is* the grounding guarantee,
enforced structurally, not just by prompting: see `evidence.py` and `service.py`),
`ai_explanation` holds the narrative, always labeled `source: "ai_generated"`. Neither the
provider nor this module ever writes to `computed` — it is built once, from Phase 02-04's
own outputs, before any provider is called, and returned unmodified.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel


class AICapability(str, Enum):
    DATASET_SUMMARY = "dataset_summary"
    QUALITY_EXPLANATION = "quality_explanation"
    COLUMN_INSIGHT = "column_insight"
    CORRELATION_EXPLANATION = "correlation_explanation"
    ML_EXPLANATION = "ml_explanation"


class QuestionCategory(str, Enum):
    DETERMINISTIC_LOOKUP = "deterministic_lookup"
    EXPLANATION = "explanation"
    ANALYTICAL_INTERPRETATION = "analytical_interpretation"
    UNSUPPORTED = "unsupported"


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


class AIStatusResponse(BaseModel):
    enabled: bool
    provider: str
    model: str | None
    available: bool
    reason: str | None
    """Why `available` is false, if it is — e.g. "AI provider is not configured." Never
    includes the API key or any other secret, by construction (this model has no field
    capable of holding one)."""


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class AIAnalyzeRequest(BaseModel):
    capability: AICapability
    column_name: str | None = None
    """Required for `column_insight`, ignored otherwise."""
    ml_result: dict[str, Any] | None = None
    """Required for `ml_explanation`. There is no model-persistence layer (ADR-013), so
    the caller supplies the already-computed Phase 04 `ModelResult` payload directly —
    this module never re-runs training itself."""


class AIQueryRequest(BaseModel):
    question: str
    ml_result: dict[str, Any] | None = None
    """Optional — supplied only if the question may relate to a Phase 04 result the
    caller already has."""


# ---------------------------------------------------------------------------
# The AI explanation block (source: "ai_generated", always)
# ---------------------------------------------------------------------------


class AIExplanation(BaseModel):
    source: Literal["ai_generated"] = "ai_generated"
    provider: str
    model: str | None
    text: str
    generated_at: datetime


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class AIAnalyzeResponse(BaseModel):
    dataset_id: str
    capability: AICapability
    computed: dict[str, Any]
    """The exact deterministic evidence this response is grounded in — copied verbatim
    from Phase 02-04's own output, byte-for-byte identical regardless of what the
    provider returns as `ai_explanation.text`. This is the enforceable part of the
    grounding contract; see `test_ai_grounding.py`."""
    evidence_sources: list[str]
    ai_explanation: AIExplanation | None
    grounded: bool
    limitations: list[str]
    available: bool
    reason: str | None


class AIQueryResponse(BaseModel):
    dataset_id: str
    question: str
    question_category: QuestionCategory
    computed: dict[str, Any]
    evidence_sources: list[str]
    ai_explanation: AIExplanation | None
    grounded: bool
    limitations: list[str]
    available: bool
    reason: str | None
