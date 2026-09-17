"""Integration tests for the `/api/v1/ml/task-types` and
`/api/v1/datasets/{id}/ml/{validate-target,train,compare}` endpoints.
"""

from fastapi.testclient import TestClient

from tests.conftest import FIXTURES_DIR


def _upload(client: TestClient, fixture_name: str) -> str:
    response = client.post(
        "/api/v1/datasets",
        files={"file": (fixture_name, (FIXTURES_DIR / fixture_name).read_bytes(), "text/csv")},
    )
    assert response.status_code == 201
    return response.json()["id"]


class TestTaskTypesEndpoint:
    def test_lists_all_three_task_types(self, client: TestClient) -> None:
        response = client.get("/api/v1/ml/task-types")
        assert response.status_code == 200
        task_types = {t["task_type"] for t in response.json()["task_types"]}
        assert task_types == {"binary_classification", "multiclass_classification", "regression"}

    def test_each_task_type_lists_supported_models(self, client: TestClient) -> None:
        response = client.get("/api/v1/ml/task-types")
        for info in response.json()["task_types"]:
            assert len(info["supported_models"]) > 0


class TestValidateTargetEndpoint:
    def test_valid_binary_target_returns_suggestion(self, client: TestClient) -> None:
        dataset_id = _upload(client, "ml_classification.csv")
        response = client.post(
            f"/api/v1/datasets/{dataset_id}/ml/validate-target", json={"target_column": "outcome"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["is_suggestion"] is True
        assert body["suggested_task"] == "binary_classification"

    def test_unknown_dataset_returns_404(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/datasets/does-not-exist/ml/validate-target", json={"target_column": "x"}
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "dataset_not_found"

    def test_unknown_column_returns_404(self, client: TestClient) -> None:
        dataset_id = _upload(client, "ml_classification.csv")
        response = client.post(
            f"/api/v1/datasets/{dataset_id}/ml/validate-target",
            json={"target_column": "does_not_exist"},
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "target_not_found"


class TestTrainEndpoint:
    def test_trains_a_binary_classifier(self, client: TestClient) -> None:
        dataset_id = _upload(client, "ml_classification.csv")
        response = client.post(
            f"/api/v1/datasets/{dataset_id}/ml/train",
            json={
                "target_column": "outcome",
                "task_type": "binary_classification",
                "model_name": "logistic_regression",
                "test_size": 0.2,
                "random_state": 42,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["model_name"] == "logistic_regression"
        assert "accuracy" in body["metrics"]
        assert body["confusion_matrix"] is not None

    def test_trains_a_regressor(self, client: TestClient) -> None:
        dataset_id = _upload(client, "ml_regression.csv")
        response = client.post(
            f"/api/v1/datasets/{dataset_id}/ml/train",
            json={
                "target_column": "price",
                "task_type": "regression",
                "model_name": "linear_regression",
                "test_size": 0.2,
                "random_state": 42,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert "rmse" in body["metrics"]
        assert body["confusion_matrix"] is None

    def test_trains_a_multiclass_classifier(self, client: TestClient) -> None:
        dataset_id = _upload(client, "ml_multiclass.csv")
        response = client.post(
            f"/api/v1/datasets/{dataset_id}/ml/train",
            json={
                "target_column": "tier",
                "task_type": "multiclass_classification",
                "model_name": "random_forest_classifier",
                "test_size": 0.2,
                "random_state": 42,
            },
        )
        assert response.status_code == 200
        assert len(response.json()["confusion_matrix"]["labels"]) == 4

    def test_invalid_model_for_task_returns_structured_400(self, client: TestClient) -> None:
        dataset_id = _upload(client, "ml_regression.csv")
        response = client.post(
            f"/api/v1/datasets/{dataset_id}/ml/train",
            json={
                "target_column": "price",
                "task_type": "regression",
                "model_name": "logistic_regression",  # classification model on a regression task
                "test_size": 0.2,
                "random_state": 42,
            },
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "invalid_model_for_task"

    def test_invalid_target_returns_structured_error(self, client: TestClient) -> None:
        dataset_id = _upload(client, "ml_classification.csv")
        response = client.post(
            f"/api/v1/datasets/{dataset_id}/ml/train",
            json={
                "target_column": "does_not_exist",
                "task_type": "binary_classification",
                "model_name": "logistic_regression",
            },
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "target_not_found"

    def test_insufficient_rows_returns_structured_400(self, client: TestClient) -> None:
        dataset_id = _upload(client, "header_only.csv")  # 0 rows, from Phase 02 fixtures
        response = client.post(
            f"/api/v1/datasets/{dataset_id}/ml/train",
            json={
                "target_column": "id",
                "task_type": "regression",
                "model_name": "linear_regression",
            },
        )
        assert response.status_code == 400

    def test_repeated_training_is_deterministic(self, client: TestClient) -> None:
        dataset_id = _upload(client, "ml_classification.csv")
        payload = {
            "target_column": "outcome",
            "task_type": "binary_classification",
            "model_name": "random_forest_classifier",
            "test_size": 0.2,
            "random_state": 42,
        }
        first = client.post(f"/api/v1/datasets/{dataset_id}/ml/train", json=payload).json()
        second = client.post(f"/api/v1/datasets/{dataset_id}/ml/train", json=payload).json()
        assert first["metrics"] == second["metrics"]
        assert first["confusion_matrix"] == second["confusion_matrix"]


class TestCompareEndpoint:
    def test_compares_multiple_models(self, client: TestClient) -> None:
        dataset_id = _upload(client, "ml_classification.csv")
        response = client.post(
            f"/api/v1/datasets/{dataset_id}/ml/compare",
            json={
                "target_column": "outcome",
                "task_type": "binary_classification",
                "model_names": ["logistic_regression", "random_forest_classifier"],
                "test_size": 0.2,
                "random_state": 42,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["results"]) == 2
        assert "winner" not in body
        assert "best_model" not in body

    def test_unknown_dataset_returns_404(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/datasets/does-not-exist/ml/compare",
            json={
                "target_column": "x",
                "task_type": "regression",
                "model_names": ["linear_regression"],
            },
        )
        assert response.status_code == 404


class TestOpenApiSchema:
    def test_ml_paths_are_registered(self, client: TestClient) -> None:
        schema = client.get("/openapi.json").json()
        paths = schema["paths"]
        assert "/api/v1/ml/task-types" in paths
        assert "/api/v1/datasets/{dataset_id}/ml/validate-target" in paths
        assert "/api/v1/datasets/{dataset_id}/ml/train" in paths
        assert "/api/v1/datasets/{dataset_id}/ml/compare" in paths
