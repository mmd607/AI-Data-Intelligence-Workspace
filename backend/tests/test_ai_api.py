"""Integration tests for `/api/v1/ai/status` and
`/api/v1/datasets/{id}/ai/{analyze,query}`.
"""

from fastapi.testclient import TestClient

from app.api.ai import get_ai_provider
from app.main import app
from tests.conftest import FIXTURES_DIR, FakeProvider


def _upload(client: TestClient, fixture_name: str) -> str:
    response = client.post(
        "/api/v1/datasets",
        files={"file": (fixture_name, (FIXTURES_DIR / fixture_name).read_bytes(), "text/csv")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _with_fake_provider(client: TestClient, provider: FakeProvider):
    app.dependency_overrides[get_ai_provider] = lambda: provider
    return client


class TestStatusEndpoint:
    def test_default_offline_status(self, client: TestClient) -> None:
        response = client.get("/api/v1/ai/status")
        assert response.status_code == 200
        body = response.json()
        assert body["enabled"] is True
        assert body["provider"] == "offline"
        assert body["available"] is True

    def test_status_never_exposes_a_secret(self, client: TestClient) -> None:
        response = client.get("/api/v1/ai/status")
        assert "api_key" not in response.text.lower()
        assert "secret" not in response.text.lower()

    def test_disabled_provider_status(self, client: TestClient) -> None:
        _with_fake_provider(client, None)
        try:
            response = client.get("/api/v1/ai/status")
            assert response.status_code == 200
        finally:
            app.dependency_overrides.pop(get_ai_provider, None)


class TestAnalyzeEndpoint:
    def test_dataset_summary_with_offline_provider(self, client: TestClient) -> None:
        dataset_id = _upload(client, "profiling_dataset.csv")
        response = client.post(
            f"/api/v1/datasets/{dataset_id}/ai/analyze", json={"capability": "dataset_summary"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["available"] is True
        assert body["ai_explanation"]["source"] == "ai_generated"
        assert body["computed"]["row_count"] == 10
        assert body["grounded"] is True

    def test_column_insight_requires_column_name(self, client: TestClient) -> None:
        dataset_id = _upload(client, "profiling_dataset.csv")
        response = client.post(
            f"/api/v1/datasets/{dataset_id}/ai/analyze", json={"capability": "column_insight"}
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "column_name_required"

    def test_column_insight_unknown_column(self, client: TestClient) -> None:
        dataset_id = _upload(client, "profiling_dataset.csv")
        response = client.post(
            f"/api/v1/datasets/{dataset_id}/ai/analyze",
            json={"capability": "column_insight", "column_name": "does_not_exist"},
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "column_not_found"

    def test_ml_explanation_without_ml_result_returns_structured_400(
        self, client: TestClient
    ) -> None:
        dataset_id = _upload(client, "profiling_dataset.csv")
        response = client.post(
            f"/api/v1/datasets/{dataset_id}/ai/analyze", json={"capability": "ml_explanation"}
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "ml_result_required"

    def test_ml_explanation_with_valid_ml_result(self, client: TestClient) -> None:
        dataset_id = _upload(client, "profiling_dataset.csv")
        ml_result = {
            "task_type": "regression",
            "target_column": "age",
            "model_name": "linear_regression",
            "feature_columns": ["category"],
            "train_size": 8,
            "test_size_actual": 2,
            "metrics": {"rmse": 5.0, "r2": 0.5},
        }
        response = client.post(
            f"/api/v1/datasets/{dataset_id}/ai/analyze",
            json={"capability": "ml_explanation", "ml_result": ml_result},
        )
        assert response.status_code == 200
        assert response.json()["computed"]["metrics"] == {"rmse": 5.0, "r2": 0.5}

    def test_unknown_dataset_returns_structured_404(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/datasets/does-not-exist/ai/analyze", json={"capability": "dataset_summary"}
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "dataset_not_found"

    def test_provider_unavailable_returns_200_with_available_false(
        self, client: TestClient
    ) -> None:
        dataset_id = _upload(client, "profiling_dataset.csv")
        _with_fake_provider(
            client, FakeProvider(available=False, unavailable_reason="not configured")
        )
        try:
            response = client.post(
                f"/api/v1/datasets/{dataset_id}/ai/analyze", json={"capability": "dataset_summary"}
            )
            assert response.status_code == 200
            body = response.json()
            assert body["available"] is False
            assert body["reason"] == "not configured"
            assert body["computed"]["row_count"] == 10  # deterministic data still returned
        finally:
            app.dependency_overrides.pop(get_ai_provider, None)


class TestQueryEndpoint:
    def test_deterministic_lookup_question(self, client: TestClient) -> None:
        dataset_id = _upload(client, "profiling_dataset.csv")
        response = client.post(
            f"/api/v1/datasets/{dataset_id}/ai/query",
            json={"question": "How many rows are duplicated?"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["question_category"] == "deterministic_lookup"
        assert body["available"] is True

    def test_unsupported_question(self, client: TestClient) -> None:
        dataset_id = _upload(client, "profiling_dataset.csv")
        response = client.post(
            f"/api/v1/datasets/{dataset_id}/ai/query",
            json={"question": "What was the model's F1 score?"},  # no ml_result supplied
        )
        assert response.status_code == 200
        body = response.json()
        assert body["question_category"] == "unsupported"
        assert "does not contain enough information" in body["ai_explanation"]["text"]

    def test_unknown_dataset_returns_structured_404(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/datasets/does-not-exist/ai/query", json={"question": "anything"}
        )
        assert response.status_code == 404


class TestOpenApiSchema:
    def test_ai_paths_are_registered(self, client: TestClient) -> None:
        schema = client.get("/openapi.json").json()
        paths = schema["paths"]
        assert "/api/v1/ai/status" in paths
        assert "/api/v1/datasets/{dataset_id}/ai/analyze" in paths
        assert "/api/v1/datasets/{dataset_id}/ai/query" in paths
