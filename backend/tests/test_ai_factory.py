"""Tests for the provider factory — no silent fallback between providers."""

from app.ai.factory import get_provider
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.ai.providers.offline import OfflineProvider
from app.config import Settings


def test_disabled_returns_none() -> None:
    provider = get_provider(Settings(ai_provider="disabled"))
    assert provider is None


def test_offline_is_the_default() -> None:
    provider = get_provider(Settings())
    assert isinstance(provider, OfflineProvider)


def test_anthropic_returns_anthropic_provider_even_when_misconfigured() -> None:
    # No API key set — the factory still returns an AnthropicProvider instance rather
    # than silently substituting OfflineProvider; its own is_available() reports why.
    provider = get_provider(Settings(ai_provider="anthropic", ai_model="claude-test"))
    assert isinstance(provider, AnthropicProvider)
    available, reason = provider.is_available()
    assert available is False
    assert "missing API key" in reason


def test_anthropic_configured_is_available() -> None:
    from pydantic import SecretStr

    provider = get_provider(
        Settings(ai_provider="anthropic", ai_model="claude-test", ai_api_key=SecretStr("key"))
    )
    available, _ = provider.is_available()
    assert available is True
