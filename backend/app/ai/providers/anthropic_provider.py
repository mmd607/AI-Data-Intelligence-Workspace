"""A real LLM provider (Anthropic's Messages API), called directly over HTTP via `httpx`
rather than an official SDK — per `01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_PROMPT.md`
"Dependency Discipline" ("Do not add a large AI framework merely for convenience"),
`httpx` is already a project dependency (used for the FastAPI test client since Phase 01);
a direct REST call needs nothing more.

Never the default — only used when `APP_AI_PROVIDER=anthropic` is explicitly configured
with an API key (`02_DOCS/PRODUCT_SPEC.md` principle 4: the app must work without this).
"""

import json
from typing import Any

import httpx

from app.ai.errors import AIError
from app.ai.provider import AIProvider, ProviderResult
from app.ai.security import build_user_prompt

NAME = "anthropic"
_MESSAGES_PATH = "/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"
_MAX_RESPONSE_TOKENS = 1024


class AnthropicProvider(AIProvider):
    name = NAME

    def __init__(
        self, api_key: str | None, model: str, base_url: str, timeout_seconds: float
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def is_available(self) -> tuple[bool, str | None]:
        if not self._api_key:
            return False, "AI provider 'anthropic' is not configured: missing API key."
        if not self._model:
            return False, "AI provider 'anthropic' is not configured: missing model name."
        return True, None

    def generate(
        self, system_instructions: str, evidence: dict[str, Any], user_request: str
    ) -> ProviderResult:
        available, reason = self.is_available()
        if not available:
            raise AIError(
                code="ai_provider_not_configured", message=reason or "Provider not configured"
            )

        user_prompt = build_user_prompt(json.dumps(evidence, default=str), user_request)

        try:
            response = httpx.post(
                f"{self._base_url}{_MESSAGES_PATH}",
                headers={
                    "x-api-key": self._api_key or "",
                    "anthropic-version": _ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
                json={
                    "model": self._model,
                    "max_tokens": _MAX_RESPONSE_TOKENS,
                    "system": system_instructions,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
                timeout=self._timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise AIError(
                code="ai_provider_timeout", message="The AI provider timed out.", status_code=504
            ) from exc
        except httpx.RequestError as exc:
            raise AIError(
                code="ai_provider_network_error",
                message=f"Could not reach the AI provider: {exc}",
                status_code=502,
            ) from exc

        self._raise_for_error_status(response)

        try:
            body = response.json()
            text = body["content"][0]["text"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AIError(
                code="ai_provider_malformed_response",
                message="The AI provider returned a response in an unexpected format.",
                status_code=502,
            ) from exc

        return ProviderResult(text=text, provider=NAME, model=self._model)

    @staticmethod
    def _raise_for_error_status(response: httpx.Response) -> None:
        if response.status_code == 401:
            raise AIError(
                code="ai_provider_unauthorized",
                message="The AI provider rejected the API key.",
                status_code=502,
            )
        if response.status_code == 429:
            raise AIError(
                code="ai_provider_rate_limited",
                message="The AI provider is rate-limiting requests.",
                status_code=502,
            )
        if response.status_code >= 400:
            raise AIError(
                code="ai_provider_error",
                message=f"The AI provider returned an error (status {response.status_code}).",
                status_code=502,
            )
