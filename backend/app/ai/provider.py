"""The AI provider interface.

Every provider (offline or a real LLM) implements this same interface, so the rest of the
module (`service.py`) never depends on a specific vendor — per
`01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_PROMPT.md` "AI Provider Architecture": "Do NOT
hard-code the application directly to one AI vendor."

A provider's `generate()` receives only the already-built, bounded evidence dict (never
raw dataset rows, never the application's own configuration/secrets) plus system
instructions establishing the untrusted-data boundary (`security.py`) and the user's
request text. It returns narrative text only — it is never given a way to modify the
evidence itself, which is why the evidence a response is grounded in can never be altered
by a provider, regardless of what text it produces.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderResult:
    text: str
    provider: str
    model: str | None


class AIProvider(ABC):
    """Base class for every AI provider implementation."""

    name: str

    @abstractmethod
    def is_available(self) -> tuple[bool, str | None]:
        """Returns `(available, reason_if_not)`. Must never raise — a misconfigured or
        unreachable provider is a normal, expected state, not an exceptional one.
        """

    @abstractmethod
    def generate(
        self, system_instructions: str, evidence: dict[str, Any], user_request: str
    ) -> ProviderResult:
        """Produce grounded narrative text from the given evidence and request.

        Raises:
            AIError: on any failure (missing key, timeout, network error, malformed
                response, rate limiting, etc.) — never lets a raw provider-specific
                exception escape this boundary. See `app.ai.errors.AIError`.
        """
