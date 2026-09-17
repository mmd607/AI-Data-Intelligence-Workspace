"""Tests for the Phase 01 health endpoint.

Per `01_PHASES/PHASE_01_FOUNDATION/PHASE_PROMPT.md` acceptance criteria: "health endpoint
works" must be verified by an actual test, not just written code.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200() -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_shape() -> None:
    response = client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert "service" in body
    assert "environment" in body
    assert "timestamp" in body


def test_cors_headers_present_for_frontend_origin() -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_unknown_route_returns_404_not_bare_500() -> None:
    response = client.get("/does-not-exist")
    assert response.status_code == 404
