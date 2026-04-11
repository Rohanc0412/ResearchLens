from typing import Any, cast

from fastapi.testclient import TestClient

from researchlens_api.create_app import create_app

VALID_PASSWORD = "CorrectHorse1!"


def test_conversation_crud_flow(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        token, _ = _register_user(client, "casey", "casey@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        project_id = _create_project(client, headers, name="Alpha")
        create_response = client.post(
            f"/projects/{project_id}/conversations",
            json={"title": "Research Draft"},
            headers=headers,
        )
        conversation_id = create_response.json()["id"]
        list_response = client.get(f"/projects/{project_id}/conversations", headers=headers)
        get_response = client.get(f"/conversations/{conversation_id}", headers=headers)
        update_response = client.patch(
            f"/conversations/{conversation_id}",
            json={"title": "Final Draft"},
            headers=headers,
        )
        delete_response = client.delete(f"/conversations/{conversation_id}", headers=headers)

    assert create_response.status_code == 201
    assert create_response.json()["project_id"] == project_id
    assert list_response.status_code == 200
    assert [item["title"] for item in list_response.json()["items"]] == ["Research Draft"]
    assert get_response.status_code == 200
    assert get_response.json()["id"] == conversation_id
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Final Draft"
    assert delete_response.status_code == 204


def test_conversation_routes_scope_to_authenticated_tenant(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        owner_token, _ = _register_user(client, "owner", "owner@example.com")
        other_token, _ = _register_user(client, "other", "other@example.com")
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        other_headers = {"Authorization": f"Bearer {other_token}"}
        project_id = _create_project(client, owner_headers, name="Alpha")
        create_response = client.post(
            f"/projects/{project_id}/conversations",
            json={"title": "Research Draft"},
            headers=owner_headers,
        )
        conversation_id = create_response.json()["id"]
        get_response = client.get(f"/conversations/{conversation_id}", headers=other_headers)
        list_response = client.get(
            f"/projects/{project_id}/conversations",
            headers=other_headers,
        )

    assert get_response.status_code == 404
    assert list_response.status_code == 404


def test_conversation_create_rejects_invalid_project(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        token, _ = _register_user(client, "casey", "casey@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            "/projects/00000000-0000-0000-0000-000000000001/conversations",
            json={"title": "Research Draft"},
            headers=headers,
        )

    assert response.status_code == 404


def test_message_post_list_get_and_idempotent_replay(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        token, _ = _register_user(client, "casey", "casey@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        project_id = _create_project(client, headers, name="Alpha")
        conversation_id = _create_conversation(client, headers, project_id)
        first_response = client.post(
            f"/conversations/{conversation_id}/messages",
            json={
                "role": "user",
                "type": "text",
                "content_text": "Hello",
                "client_message_id": "message-1",
            },
            headers=headers,
        )
        second_response = client.post(
            f"/conversations/{conversation_id}/messages",
            json={
                "role": "user",
                "type": "text",
                "content_text": "Hello",
                "client_message_id": "message-1",
            },
            headers=headers,
        )
        second_message = client.post(
            f"/conversations/{conversation_id}/messages",
            json={
                "role": "user",
                "type": "text",
                "content_text": "Follow up",
            },
            headers=headers,
        )
        list_response = client.get(f"/conversations/{conversation_id}/messages", headers=headers)
        message_id = first_response.json()["id"]
        get_response = client.get(
            f"/conversations/{conversation_id}/messages/{message_id}",
            headers=headers,
        )
        conversation_response = client.get(f"/conversations/{conversation_id}", headers=headers)

    assert first_response.status_code == 201
    assert first_response.json()["idempotent_replay"] is False
    assert second_response.status_code == 200
    assert second_response.json()["id"] == first_response.json()["id"]
    assert second_response.json()["idempotent_replay"] is True
    assert second_message.status_code == 201
    assert list_response.status_code == 200
    assert [item["content_text"] for item in list_response.json()] == ["Hello", "Follow up"]
    assert get_response.status_code == 200
    assert get_response.json()["id"] == message_id
    assert conversation_response.status_code == 200
    assert conversation_response.json()["last_message_at"] is not None


def test_delete_conversation_cascades_messages(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        token, _ = _register_user(client, "casey", "casey@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        project_id = _create_project(client, headers, name="Alpha")
        conversation_id = _create_conversation(client, headers, project_id)
        message_response = client.post(
            f"/conversations/{conversation_id}/messages",
            json={"role": "user", "type": "text", "content_text": "Hello"},
            headers=headers,
        )
        message_id = message_response.json()["id"]
        delete_response = client.delete(f"/conversations/{conversation_id}", headers=headers)
        get_message_response = client.get(
            f"/conversations/{conversation_id}/messages/{message_id}",
            headers=headers,
        )

    assert delete_response.status_code == 204
    assert get_message_response.status_code == 404


def test_run_trigger_route_is_a_compatibility_alias_for_run_creation(
    migrated_database_url: str,
) -> None:
    with TestClient(create_app()) as client:
        token, _ = _register_user(client, "casey", "casey@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        project_id = _create_project(client, headers, name="Alpha")
        conversation_id = _create_conversation(client, headers, project_id)
        message_response = client.post(
            f"/conversations/{conversation_id}/messages",
            json={"role": "user", "type": "text", "content_text": "Hello"},
            headers=headers,
        )
        message_id = message_response.json()["id"]
        trigger_response = client.post(
            f"/conversations/{conversation_id}/run-triggers",
            json={
                "source_message_id": message_id,
                "request_text": "Start a run for this thread",
                "client_request_id": "request-1",
            },
            headers=headers,
        )

    assert trigger_response.status_code == 201
    assert trigger_response.json()["idempotent_replay"] is False
    assert trigger_response.json()["run"]["conversation_id"] == conversation_id
    assert trigger_response.json()["run"]["project_id"] == project_id
    assert trigger_response.json()["run"]["status"] == "queued"


def _register_user(client: TestClient, username: str, email: str) -> tuple[str, str]:
    response = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": VALID_PASSWORD},
    )
    body = cast(dict[str, Any], response.json())
    user = cast(dict[str, Any], body["user"])
    return cast(str, body["access_token"]), cast(str, user["user_id"])


def _create_project(client: TestClient, headers: dict[str, str], *, name: str) -> str:
    response = client.post(
        "/projects",
        json={"name": name, "description": None},
        headers=headers,
    )
    body = cast(dict[str, Any], response.json())
    return cast(str, body["id"])


def _create_conversation(client: TestClient, headers: dict[str, str], project_id: str) -> str:
    response = client.post(
        f"/projects/{project_id}/conversations",
        json={"title": "Research Draft"},
        headers=headers,
    )
    body = cast(dict[str, Any], response.json())
    return cast(str, body["id"])
