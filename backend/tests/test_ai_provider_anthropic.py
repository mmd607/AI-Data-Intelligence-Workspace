"""Tests for the real (Anthropic) provider adapter — every HTTP call is mocked; this
suite NEVER makes a real network request, per
`01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_PROMPT.md` section 21 ("NEVER make tests depend on
a live external LLM API").
"""

from unittest.mock import patch

import httpx
import pytest

from app.ai.errors import AIError
from app.ai.providers.anthropic_provider import AnthropicProvider


def _provider(api_key: str | None = "test-key", model: str = "claude-test") -> AnthropicProvider:
    return AnthropicProvider(
        api_key=api_key, model=model, base_url="https://example.invalid", timeout_seconds=5.0
    )


class TestAvailability:
    def test_missing_api_key_is_unavailable(self) -> None:
        provider = _provider(api_key=None)
        available, reason = provider.is_available()
        assert available is False
        assert "missing API key" in reason

    def test_missing_model_is_unavailable(self) -> None:
        provider = _provider(model="")
        available, reason = provider.is_available()
        assert available is False
        assert "missing model" in reason

    def test_configured_provider_is_available(self) -> None:
        provider = _provider()
        available, reason = provider.is_available()
        assert available is True
        assert reason is None


class TestGenerateFailureModes:
    def test_missing_api_key_raises_before_any_network_call(self) -> None:
        provider = _provider(api_key=None)
        with patch("httpx.post") as mock_post:
            with pytest.raises(AIError) as exc_info:
                provider.generate("system", {"a": 1}, "question")
        mock_post.assert_not_called()
        assert exc_info.value.code == "ai_provider_not_configured"

    def test_timeout_raises_structured_error(self) -> None:
        provider = _provider()
        with patch("httpx.post", side_effect=httpx.TimeoutException("timed out")):
            with pytest.raises(AIError) as exc_info:
                provider.generate("system", {"a": 1}, "question")
        assert exc_info.value.code == "ai_provider_timeout"

    def test_network_error_raises_structured_error(self) -> None:
        provider = _provider()
        with patch("httpx.post", side_effect=httpx.ConnectError("no route")):
            with pytest.raises(AIError) as exc_info:
                provider.generate("system", {"a": 1}, "question")
        assert exc_info.value.code == "ai_provider_network_error"

    def test_unauthorized_raises_structured_error(self) -> None:
        provider = _provider()
        fake_response = httpx.Response(401, request=httpx.Request("POST", "https://example.invalid"))
        with patch("httpx.post", return_value=fake_response):
            with pytest.raises(AIError) as exc_info:
                provider.generate("system", {"a": 1}, "question")
        assert exc_info.value.code == "ai_provider_unauthorized"

    def test_rate_limited_raises_structured_error(self) -> None:
        provider = _provider()
        fake_response = httpx.Response(429, request=httpx.Request("POST", "https://example.invalid"))
        with patch("httpx.post", return_value=fake_response):
            with pytest.raises(AIError) as exc_info:
                provider.generate("system", {"a": 1}, "question")
        assert exc_info.value.code == "ai_provider_rate_limited"

    def test_server_error_raises_structured_error(self) -> None:
        provider = _provider()
        fake_response = httpx.Response(500, request=httpx.Request("POST", "https://example.invalid"))
        with patch("httpx.post", return_value=fake_response):
            with pytest.raises(AIError) as exc_info:
                provider.generate("system", {"a": 1}, "question")
        assert exc_info.value.code == "ai_provider_error"

    def test_malformed_response_body_raises_structured_error(self) -> None:
        provider = _provider()
        fake_response = httpx.Response(
            200, json={"unexpected": "shape"}, request=httpx.Request("POST", "https://example.invalid")
        )
        with patch("httpx.post", return_value=fake_response):
            with pytest.raises(AIError) as exc_info:
                provider.generate("system", {"a": 1}, "question")
        assert exc_info.value.code == "ai_provider_malformed_response"


class TestSuccessfulGeneration:
    def test_returns_the_provider_text_on_success(self) -> None:
        provider = _provider()
        fake_response = httpx.Response(
            200,
            json={"content": [{"type": "text", "text": "This is the generated explanation."}]},
            request=httpx.Request("POST", "https://example.invalid"),
        )
        with patch("httpx.post", return_value=fake_response) as mock_post:
            result = provider.generate("system instructions", {"row_count": 10}, "explain")
        assert result.text == "This is the generated explanation."
        assert result.provider == "anthropic"
        assert result.model == "claude-test"
        mock_post.assert_called_once()

    def test_api_key_sent_as_header_never_in_body_text(self) -> None:
        provider = _provider(api_key="super-secret-key")
        fake_response = httpx.Response(
            200,
            json={"content": [{"type": "text", "text": "ok"}]},
            request=httpx.Request("POST", "https://example.invalid"),
        )
        with patch("httpx.post", return_value=fake_response) as mock_post:
            provider.generate("system", {"a": 1}, "question")
        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["x-api-key"] == "super-secret-key"
        assert "super-secret-key" not in str(kwargs["json"])

    def test_evidence_is_sent_as_data_not_as_system_instructions(self) -> None:
        provider = _provider()
        fake_response = httpx.Response(
            200,
            json={"content": [{"type": "text", "text": "ok"}]},
            request=httpx.Request("POST", "https://example.invalid"),
        )
        with patch("httpx.post", return_value=fake_response) as mock_post:
            provider.generate("SYSTEM_RULES_HERE", {"row_count": 42}, "explain")
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["system"] == "SYSTEM_RULES_HERE"
        assert "42" in kwargs["json"]["messages"][0]["content"]
