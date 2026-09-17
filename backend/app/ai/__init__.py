"""Optional, grounded AI analytics layer.

Scope, per `01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_PROMPT.md` and this phase's Core
Principle: the deterministic pipeline (Phases 02-04) remains the sole source of truth.
This module never computes a statistic, metric, or correlation itself — it only builds a
bounded, deterministic evidence context from what those phases already computed, and asks
an AI provider (an offline template renderer by default, or a real LLM if explicitly
configured) to narrate it in natural language. The provider may explain; it may never
invent or alter a number. See `evidence.py` for how that guarantee is enforced at the API
contract level, not just by prompting.
"""
