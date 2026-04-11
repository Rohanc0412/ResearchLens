from typing import Any, cast

from fastapi.testclient import TestClient

from researchlens_api.create_app import create_app

VALID_PASSWORD = "CorrectHorse1!"


def test_create_run_idempotent_replay_and_compatibility_route(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        token, _ = _register_user(client, "casey", "casey@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        project_id = _create_project(client, headers, name="Alpha")
        conversation_id = _create_conversation(client, headers, project_id)
        message_id = _create_message(client, headers, conversation_id)

        first_response = client.post(
            f"/conversations/{conversation_id}/runs",
            json={
                "source_message_id": message_id,
                "request_text": "Start a run",
                "client_request_id": "request-1",
            },
            headers=headers,
        )
        second_response = client.post(
            f"/conversations/{conversation_id}/runs",
            json={
                "source_message_id": message_id,
                "request_text": "Start a run",
                "client_request_id": "request-1",
            },
            headers=headers,
        )
        compatibility_response = client.post(
            f"/conversations/{conversation_id}/run-triggers",
            json={
                "source_message_id": message_id,
                "request_text": "Start another run",
                "client_request_id": "request-2",
            },
            headers=headers,
        )

    assert first_response.status_code == 201
    assert first_response.json()["idempotent_replay"] is False
    assert first_response.json()["run"]["conversation_id"] == conversation_id
    assert first_response.json()["run"]["display_status"] == "Waiting"
    assert second_response.status_code == 200
    assert second_response.json()["idempotent_replay"] is True
    assert second_response.json()["run"]["id"] == first_response.json()["run"]["id"]
    assert compatibility_response.status_code == 201
    assert "run" in compatibility_response.json()
    assert compatibility_response.json()["run"]["conversation_id"] == conversation_id


def test_cancel_queued_run_returns_stopped_state_and_human_events(
    migrated_database_url: str,
) -> None:
    with TestClient(create_app()) as client:
        token, _ = _register_user(client, "casey", "casey@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        project_id = _create_project(client, headers, name="Alpha")
        conversation_id = _create_conversation(client, headers, project_id)

        create_response = client.post(
            f"/conversations/{conversation_id}/runs",
            json={"request_text": "Start a run"},
            headers=headers,
        )
        run_id = create_response.json()["run"]["id"]
        cancel_response = client.post(f"/runs/{run_id}/cancel", headers=headers)
        events_response = client.get(f"/runs/{run_id}/events", headers=headers)

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "canceled"
    assert cancel_response.json()["display_status"] == "Stopped"
    assert cancel_response.json()["can_stop"] is False
    assert [event["event_number"] for event in events_response.json()] == [1, 2, 3, 4]
    assert events_response.json()[-1]["message"] == "Run stopped before work began"
    assert events_response.json()[-1]["display_status"] == "Stopped"
    assert events_response.json()[0]["message"] == "Run created"


def test_run_event_sse_reconnect_only_returns_newer_events(
    migrated_database_url: str,
) -> None:
    with TestClient(create_app()) as client:
        token, _ = _register_user(client, "casey", "casey@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        project_id = _create_project(client, headers, name="Alpha")
        conversation_id = _create_conversation(client, headers, project_id)
        create_response = client.post(
            f"/conversations/{conversation_id}/runs",
            json={"request_text": "Start a run"},
            headers=headers,
        )
        run_id = create_response.json()["run"]["id"]
        client.post(f"/runs/{run_id}/cancel", headers=headers)

        with client.stream(
            "GET",
            f"/runs/{run_id}/events",
            headers={
                **headers,
                "Accept": "text/event-stream",
                "Last-Event-ID": "2",
            },
        ) as response:
            lines = [line for line in response.iter_lines() if line]

    assert response.status_code == 200
    joined = "\n".join(lines)
    assert "id: 3" in joined
    assert "id: 4" in joined
    assert "id: 1" not in joined
    assert '"message": "Run stopped before work began"' in joined


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


def _create_message(client: TestClient, headers: dict[str, str], conversation_id: str) -> str:
    response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={"role": "user", "type": "text", "content_text": "Hello"},
        headers=headers,
    )
    body = cast(dict[str, Any], response.json())
    return cast(str, body["id"])
