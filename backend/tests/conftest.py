"""Shared test fixtures for the ingestion test suite."""

import io
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.datasets import get_storage_service
from app.ingestion.storage import StorageService
from app.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


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
