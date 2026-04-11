from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from researchlens_api.create_app import create_app


def test_api_startup_smoke(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    with TestClient(create_app()) as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "phase": "phase-5",
        "service": "researchlens",
        "environment": "test",
    }
