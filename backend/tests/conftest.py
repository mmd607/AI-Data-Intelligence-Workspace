"""Shared test fixtures for the whole backend test suite."""

import io
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.ai.errors import AIError
from app.ai.provider import AIProvider, ProviderResult
from app.api.datasets import get_storage_service
from app.ingestion.storage import StorageService
from app.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FakeProvider(AIProvider):
    """A controllable `AIProvider` test double — never makes a network call.

    - `fixed_text`: what `generate()` returns as narrative text (default: an obviously
      fake sentence, deliberately unrelated to any real evidence, so tests that check the
      grounding guarantee can prove `computed` never echoes provider text).
    - `available`/`unavailable_reason`: controls `is_available()`.
    - `raise_error`: if set, `generate()` raises this `AIError` instead of returning.
    """

    name = "fake"

    def __init__(
        self,
        fixed_text: str = "FABRICATED: the answer is 51.2 and everything is fine.",
        available: bool = True,
        unavailable_reason: str | None = None,
        raise_error: AIError | None = None,
    ) -> None:
        self.fixed_text = fixed_text
        self._available = available
        self._unavailable_reason = unavailable_reason
        self.raise_error = raise_error
        self.last_evidence: dict[str, Any] | None = None
        self.last_system_instructions: str | None = None
        self.last_user_request: str | None = None

    def is_available(self) -> tuple[bool, str | None]:
        return self._available, self._unavailable_reason

    def generate(
        self, system_instructions: str, evidence: dict[str, Any], user_request: str
    ) -> ProviderResult:
        self.last_evidence = evidence
        self.last_system_instructions = system_instructions
        self.last_user_request = user_request
        if self.raise_error is not None:
            raise self.raise_error
        return ProviderResult(text=self.fixed_text, provider=self.name, model="fake-model")


@pytest.fixture
def storage_dir(tmp_path: Path) -> Path:
    """An isolated, per-test storage directory — never the real `backend/data/uploads/`."""
    return tmp_path / "uploads"


@pytest.fixture
def client(storage_dir: Path) -> Iterator[TestClient]:
    def _override_storage() -> StorageService:
        return StorageService(base_dir=storage_dir)

    app.dependency_overrides[get_storage_service] = _override_storage
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_storage_service, None)


def generate_large_csv_bytes(num_rows: int = 5000) -> bytes:
    """A deterministic "large-ish" CSV generated in memory — never committed to git, per
    `02_DOCS/TESTING_STRATEGY.md` §7 (only small, purpose-built fixtures are committed).
    """
    buffer = io.StringIO()
    buffer.write("id,category,value\n")
    categories = ["a", "b", "c", "d"]
    for i in range(num_rows):
        buffer.write(f"{i},{categories[i % len(categories)]},{i * 1.5}\n")
    return buffer.getvalue().encode("utf-8")
