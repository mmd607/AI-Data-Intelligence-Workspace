"""Builds the configured `AIProvider` from application settings.

No silent fallback between providers: if `APP_AI_PROVIDER=anthropic` is configured but
misconfigured (missing key/model), `get_provider()` still returns an `AnthropicProvider`
instance — its `is_available()` correctly reports why it can't be used, and `service.py`
surfaces that clearly rather than silently substituting the offline provider's output
under the "anthropic" name. See `02_DOCS/decisions/DECISIONS_LOG.md` ADR-014.
"""

from app.ai.provider import AIProvider
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.ai.providers.offline import OfflineProvider
from app.config import Settings


def get_provider(settings: Settings) -> AIProvider | None:
    """Returns `None` only when `ai_provider == "disabled"` — the AI layer is fully off.
    Otherwise always returns a provider instance; check `.is_available()` for whether it
    can actually be used right now.
    """
    if settings.ai_provider == "disabled":
        return None
    if settings.ai_provider == "anthropic":
        api_key = settings.ai_api_key.get_secret_value() if settings.ai_api_key else None
        return AnthropicProvider(
            api_key=api_key,
            model=settings.ai_model,
            base_url=settings.ai_base_url,
            timeout_seconds=settings.ai_timeout_seconds,
        )
    return OfflineProvider()
