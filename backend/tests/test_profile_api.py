"""Integration tests for the `/api/v1/datasets/{id}/{profile,quality,columns,correlation,
distribution}` endpoints, per
`01_PHASES/PHASE_03_DATA_PROFILING_VISUALIZATION/PHASE_PROMPT.md` "Testing".
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


class TestDatasetProfileEndpoint:
    def test_profile_matches_known_dataset_facts(self, client: TestClient) -> None:
        dataset_id = _upload(client, "profiling_dataset.csv")
        response = client.get(f"/api/v1/datasets/{dataset_id}/profile")

        assert response.status_code == 200
        body = response.json()
        assert body["row_count"] == 10
        assert body["column_count"] == 4
        assert body["duplicate_row_count"] == 1
        assert body["missing"]["total_missing_cells"] == 1
        assert len(body["columns"]) == 4

        age_column = next(c for c in body["columns"] if c["name"] == "age")
        assert age_column["semantic_type"] == "numeric"
        assert age_column["numeric_stats"] is not None
        assert age_column["null_count"] == 1

        category_column = next(c for c in body["columns"] if c["name"] == "category")
        assert category_column["semantic_type"] == "categorical"
        assert category_column["categorical_stats"]["cardinality"] == 3

    def test_profile_is_deterministic_across_repeated_calls(self, client: TestClient) -> None:
        dataset_id = _upload(client, "profiling_dataset.csv")
        first = client.get(f"/api/v1/datasets/{dataset_id}/profile").json()
        second = client.get(f"/api/v1/datasets/{dataset_id}/profile").json()
        first.pop("generated_at")
        second.pop("generated_at")
        assert first == second

    def test_unknown_dataset_returns_structured_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/datasets/does-not-exist/profile")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "dataset_not_found"

    def test_header_only_dataset_profiles_as_empty_without_crashing(
        self, client: TestClient
    ) -> None:
        dataset_id = _upload(client, "header_only.csv")  # Phase 02 fixture: valid, 0 rows
        response = client.get(f"/api/v1/datasets/{dataset_id}/profile")
        assert response.status_code == 200
        body = response.json()
        assert body["row_count"] == 0
        assert body["column_count"] == 4


class TestQualityEndpoint:
    def test_quality_flags_duplicates_and_missing(self, client: TestClient) -> None:
        dataset_id = _upload(client, "profiling_dataset.csv")
        response = client.get(f"/api/v1/datasets/{dataset_id}/quality")
        assert response.status_code == 200
        codes = {f["code"] for f in response.json()["findings"]}
        assert "duplicate_rows" in codes
        assert "missing_values" in codes

    def test_quality_flags_constant_and_near_constant_columns(self, client: TestClient) -> None:
        dataset_id = _upload(client, "profiling_constant.csv")
        response = client.get(f"/api/v1/datasets/{dataset_id}/quality")
        codes = {f["code"] for f in response.json()["findings"]}
        assert "constant_column" in codes
        assert "near_constant_column" in codes

    def test_quality_flags_infinite_and_unexpected_negative_values(
        self, client: TestClient
    ) -> None:
        dataset_id = _upload(client, "profiling_quality_edge.csv")
        response = client.get(f"/api/v1/datasets/{dataset_id}/quality")
        codes = {f["code"] for f in response.json()["findings"]}
        assert "infinite_values" in codes
        assert "unexpected_negative_values" in codes

    def test_header_only_dataset_reports_empty_dataset_finding(self, client: TestClient) -> None:
        dataset_id = _upload(client, "header_only.csv")
        response = client.get(f"/api/v1/datasets/{dataset_id}/quality")
        codes = {f["code"] for f in response.json()["findings"]}
        assert "empty_dataset" in codes

    def test_unknown_dataset_returns_structured_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/datasets/does-not-exist/quality")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "dataset_not_found"


class TestColumnProfileEndpoint:
    def test_known_column_returns_its_profile(self, client: TestClient) -> None:
        dataset_id = _upload(client, "profiling_dataset.csv")
        response = client.get(f"/api/v1/datasets/{dataset_id}/columns/age")
        assert response.status_code == 200
        assert response.json()["name"] == "age"
        assert response.json()["semantic_type"] == "numeric"

    def test_unknown_column_returns_structured_404(self, client: TestClient) -> None:
        dataset_id = _upload(client, "profiling_dataset.csv")
        response = client.get(f"/api/v1/datasets/{dataset_id}/columns/does_not_exist")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "column_not_found"

    def test_unknown_dataset_returns_structured_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/datasets/does-not-exist/columns/age")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "dataset_not_found"


class TestCorrelationEndpoint:
    def test_single_numeric_column_is_insufficient_data(self, client: TestClient) -> None:
        # profiling_dataset.csv has exactly one numeric column ("age").
        dataset_id = _upload(client, "profiling_dataset.csv")
        response = client.get(f"/api/v1/datasets/{dataset_id}/correlation")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "insufficient_data"
        assert body["eligible_columns"] == ["age"]

    def test_multiple_numeric_columns_computes_pairs(self, client: TestClient) -> None:
        dataset_id = _upload(client, "profiling_quality_edge.csv")  # age, ratio: both numeric
        response = client.get(f"/api/v1/datasets/{dataset_id}/correlation")
        body = response.json()
        assert set(body["eligible_columns"]) == {"age", "ratio"}

    def test_unknown_dataset_returns_structured_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/datasets/does-not-exist/correlation")
        assert response.status_code == 404


class TestDistributionEndpoint:
    def test_numeric_column_gets_bins_non_numeric_are_skipped(self, client: TestClient) -> None:
        dataset_id = _upload(client, "profiling_dataset.csv")
        response = client.get(f"/api/v1/datasets/{dataset_id}/distribution")
        assert response.status_code == 200
        body = response.json()
        columns = [c["column"] for c in body["columns"]]
        assert "age" in columns
        assert "category" in body["skipped_columns"]

    def test_unknown_dataset_returns_structured_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/datasets/does-not-exist/distribution")
        assert response.status_code == 404


class TestOpenApiSchema:
    def test_profiling_paths_are_registered(self, client: TestClient) -> None:
        schema = client.get("/openapi.json").json()
        paths = schema["paths"]
        assert "/api/v1/datasets/{dataset_id}/profile" in paths
        assert "/api/v1/datasets/{dataset_id}/quality" in paths
        assert "/api/v1/datasets/{dataset_id}/columns/{column_name}" in paths
        assert "/api/v1/datasets/{dataset_id}/correlation" in paths
        assert "/api/v1/datasets/{dataset_id}/distribution" in paths
