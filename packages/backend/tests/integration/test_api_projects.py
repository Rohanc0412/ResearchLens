from fastapi.testclient import TestClient

from researchlens_api.create_app import create_app


def test_api_projects_crud_flow(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        create_response = client.post(
            "/projects",
            json={"name": "Alpha", "description": "demo"},
        )
        list_response = client.get("/projects")
        project_id = create_response.json()["id"]
        rename_response = client.patch(f"/projects/{project_id}", json={"name": "Beta"})
        delete_response = client.delete(f"/projects/{project_id}")

    assert create_response.status_code == 201
    assert create_response.headers["X-Request-ID"]
    assert create_response.json()["name"] == "Alpha"
    assert list_response.status_code == 200
    assert [item["name"] for item in list_response.json()] == ["Alpha"]
    assert rename_response.status_code == 200
    assert rename_response.json()["name"] == "Beta"
    assert delete_response.status_code == 204


def test_api_project_name_conflict_returns_409(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        first_response = client.post("/projects", json={"name": "Alpha", "description": None})
        second_response = client.post("/projects", json={"name": "Alpha", "description": None})

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["code"] == "conflict"
