from fastapi.testclient import TestClient

from researchlens_api.create_app import create_app

VALID_PASSWORD = "CorrectHorse1!"


def test_api_projects_crud_flow(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        token, user_id = _register_and_get_identity(client)
        headers = {"Authorization": f"Bearer {token}"}
        create_response = client.post(
            "/projects",
            json={"name": "Alpha", "description": "demo"},
            headers=headers,
        )
        list_response = client.get("/projects", headers=headers)
        project_id = create_response.json()["id"]
        get_response = client.get(f"/projects/{project_id}", headers=headers)
        rename_response = client.patch(
            f"/projects/{project_id}",
            json={"name": "Beta", "description": "renamed"},
            headers=headers,
        )
        delete_response = client.delete(f"/projects/{project_id}", headers=headers)

    assert create_response.status_code == 201
    assert create_response.headers["X-Request-ID"]
    assert create_response.json()["name"] == "Alpha"
    assert create_response.json()["created_by"] == user_id
    assert list_response.status_code == 200
    assert [item["name"] for item in list_response.json()] == ["Alpha"]
    assert get_response.status_code == 200
    assert get_response.json()["id"] == project_id
    assert rename_response.status_code == 200
    assert rename_response.json()["name"] == "Beta"
    assert rename_response.json()["description"] == "renamed"
    assert delete_response.status_code == 204


def test_api_project_name_conflict_returns_409(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        token, _ = _register_and_get_identity(client)
        headers = {"Authorization": f"Bearer {token}"}
        first_response = client.post(
            "/projects",
            json={"name": "Alpha", "description": None},
            headers=headers,
        )
        second_response = client.post(
            "/projects",
            json={"name": "Alpha", "description": None},
            headers=headers,
        )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["code"] == "conflict"


def test_api_projects_require_real_auth_identity(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        response = client.get("/projects")

    assert response.status_code == 401


def test_api_project_update_rejects_empty_patch(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        token, _ = _register_and_get_identity(client)
        headers = {"Authorization": f"Bearer {token}"}
        create_response = client.post(
            "/projects",
            json={"name": "Alpha", "description": None},
            headers=headers,
        )
        project_id = create_response.json()["id"]
        response = client.patch(f"/projects/{project_id}", json={}, headers=headers)

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def _register_and_get_identity(client: TestClient) -> tuple[str, str]:
    response = client.post(
        "/auth/register",
        json={"username": "casey", "email": "casey@example.com", "password": VALID_PASSWORD},
    )
    body = response.json()
    return body["access_token"], body["user"]["user_id"]
