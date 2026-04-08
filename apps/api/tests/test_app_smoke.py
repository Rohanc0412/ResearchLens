from fastapi.testclient import TestClient

from researchlens_api.create_app import create_app


def test_create_app_smoke() -> None:
    client = TestClient(create_app())

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "phase": "phase-0"}

