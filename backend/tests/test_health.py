"""Task 1 acceptance: the serving tier answers /health with 200 {"status":"ok"}."""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_banner() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "GHOST THREAD"
