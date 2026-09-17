"""Integration tests for the `/api/v1/datasets` endpoints — the full
upload → list → get flow, plus error handling, per
`01_PHASES/PHASE_02_DATA_INGESTION/PHASE_PROMPT.md` "Testing Requirements".
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from tests.conftest import FIXTURES_DIR


def _upload(client: TestClient, filename: str, content: bytes, content_type: str = "text/csv"):
    return client.post("/api/v1/datasets", files={"file": (filename, content, content_type)})


class TestUploadListGetFlow:
    def test_upload_returns_201_with_expected_metadata(self, client: TestClient) -> None:
        response = _upload(client, "valid.csv", (FIXTURES_DIR / "valid.csv").read_bytes())
        assert response.status_code == 201
        body = response.json()
        assert body["original_filename"] == "valid.csv"
        assert body["row_count"] == 3
        assert body["column_count"] == 4
        assert body["missing_value_count"] == 0
        assert body["duplicate_row_count"] == 0
        assert len(body["columns"]) == 4
        assert "id" in body and body["id"]
        assert "uploaded_at" in body

    def test_uploaded_dataset_appears_in_list(self, client: TestClient) -> None:
        upload_response = _upload(client, "valid.csv", (FIXTURES_DIR / "valid.csv").read_bytes())
        dataset_id = upload_response.json()["id"]

        list_response = client.get("/api/v1/datasets")
        assert list_response.status_code == 200
        ids = [item["id"] for item in list_response.json()]
        assert dataset_id in ids

    def test_get_by_id_returns_full_metadata(self, client: TestClient) -> None:
        upload_response = _upload(client, "valid.csv", (FIXTURES_DIR / "valid.csv").read_bytes())
        dataset_id = upload_response.json()["id"]

        get_response = client.get(f"/api/v1/datasets/{dataset_id}")
        assert get_response.status_code == 200
        assert get_response.json() == upload_response.json()

    def test_two_uploads_of_the_same_file_get_distinct_ids_but_identical_computed_fields(
        self, client: TestClient
    ) -> None:
        raw = (FIXTURES_DIR / "valid.csv").read_bytes()
        first = _upload(client, "valid.csv", raw).json()
        second = _upload(client, "valid.csv", raw).json()

        assert first["id"] != second["id"]
        computed_fields = (
            "row_count",
            "column_count",
            "missing_value_count",
            "duplicate_row_count",
            "columns",
        )
        for field in computed_fields:
            assert first[field] == second[field]


class TestGetUnknownDataset:
    def test_returns_structured_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/datasets/does-not-exist")
        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "dataset_not_found"


class TestUploadErrors:
    def test_unsupported_file_type_returns_structured_400(self, client: TestClient) -> None:
        response = _upload(client, "data.json", b'{"a": 1}', content_type="application/json")
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "unsupported_file_type"

    def test_empty_file_returns_structured_400(self, client: TestClient) -> None:
        response = _upload(client, "empty.csv", b"")
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "empty_file"

    def test_malformed_csv_returns_structured_400(self, client: TestClient) -> None:
        response = _upload(client, "malformed.csv", (FIXTURES_DIR / "malformed.csv").read_bytes())
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "malformed_csv"

    def test_nothing_is_persisted_after_a_rejected_upload(
        self, client: TestClient, storage_dir: Path
    ) -> None:
        _upload(client, "empty.csv", b"")
        assert not storage_dir.exists() or list(storage_dir.iterdir()) == []


class TestUploadSizeLimit:
    def test_oversized_file_returns_413(self, storage_dir: Path) -> None:
        from app.api.datasets import get_storage_service
        from app.ingestion.storage import StorageService

        app.dependency_overrides[get_settings] = lambda: Settings(max_upload_size_bytes=10)
        app.dependency_overrides[get_storage_service] = lambda: StorageService(base_dir=storage_dir)
        try:
            with TestClient(app) as tiny_limit_client:
                response = _upload(tiny_limit_client, "valid.csv", b"id,name\n1,Alice\n2,Bob\n")
        finally:
            app.dependency_overrides.pop(get_settings, None)
            app.dependency_overrides.pop(get_storage_service, None)

        assert response.status_code == 413
        assert response.json()["error"]["code"] == "file_too_large"


class TestPathTraversalFilename:
    def test_malicious_filename_is_sanitized_and_never_escapes_storage_dir(
        self, client: TestClient, storage_dir: Path
    ) -> None:
        response = _upload(
            client,
            "../../../etc/passwd.csv",
            (FIXTURES_DIR / "valid.csv").read_bytes(),
        )
        assert response.status_code == 201
        body = response.json()

        # The displayed filename is sanitized to a bare name.
        assert body["original_filename"] == "passwd.csv"
        assert "/" not in body["original_filename"]

        # The file was written strictly under storage_dir/<dataset_id>/, nowhere else.
        dataset_dir = storage_dir / body["id"]
        assert (dataset_dir / "original.csv").exists()
        assert list(storage_dir.iterdir()) == [dataset_dir]
