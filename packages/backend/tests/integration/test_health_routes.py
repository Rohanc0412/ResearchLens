from fastapi.testclient import TestClient

from researchlens_api.create_app import create_app


def test_healthz_returns_boot_status(sqlite_database_url: str) -> None:
    with TestClient(create_app()) as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_returns_healthy_when_db_and_schema_are_ready(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_returns_503_when_schema_is_missing(sqlite_database_url: str) -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["code"] == "infrastructure_error"
