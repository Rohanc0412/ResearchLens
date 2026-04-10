from uuid import UUID

from fastapi.testclient import TestClient

from researchlens_api.create_app import create_app

COOKIE_NAME = "researchlens_refresh"
VALID_PASSWORD = "CorrectHorse1!"


def test_register_login_refresh_me_and_logout_contracts(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        register_response = client.post(
            "/auth/register",
            json={
                "username": "Casey",
                "email": "casey@example.com",
                "password": VALID_PASSWORD,
            },
        )
        register_body = register_response.json()
        login_response = client.post(
            "/auth/login",
            json={"identifier": "casey", "password": VALID_PASSWORD},
        )
        email_login_response = client.post(
            "/auth/login",
            json={"identifier": "casey@example.com", "password": VALID_PASSWORD},
        )
        me_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {register_body['access_token']}"},
        )
        refresh_response = client.post("/auth/refresh")
        logout_response = client.post("/auth/logout")

    assert register_response.status_code == 201
    _assert_token_response_shape(register_body)
    assert register_response.cookies.get(COOKIE_NAME)
    assert login_response.status_code == 200
    _assert_token_response_shape(login_response.json())
    assert email_login_response.status_code == 200
    _assert_token_response_shape(email_login_response.json())
    assert refresh_response.status_code == 200
    _assert_token_response_shape(refresh_response.json())
    assert me_response.status_code == 200
    assert set(me_response.json()) == {"user_id", "username", "email", "tenant_id", "roles"}
    assert me_response.json()["user_id"] == register_body["user"]["user_id"]
    assert me_response.json()["username"] == "casey"
    assert me_response.json()["username"] != me_response.json()["user_id"]
    assert logout_response.status_code == 200
    assert logout_response.json() == {"status": "ok"}
    assert logout_response.cookies.get(COOKIE_NAME) is None


def test_register_rejects_duplicates_and_weak_passwords(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        first = client.post(
            "/auth/register",
            json={"username": "casey", "email": "casey@example.com", "password": VALID_PASSWORD},
        )
        duplicate_username = client.post(
            "/auth/register",
            json={"username": "casey", "email": "other@example.com", "password": VALID_PASSWORD},
        )
        duplicate_email = client.post(
            "/auth/register",
            json={"username": "other", "email": "casey@example.com", "password": VALID_PASSWORD},
        )
        weak_password = client.post(
            "/auth/register",
            json={"username": "weak", "email": "weak@example.com", "password": "weak"},
        )

    assert first.status_code == 201
    assert duplicate_username.status_code == 409
    assert duplicate_email.status_code == 409
    assert weak_password.status_code == 422


def test_login_invalid_credentials_returns_401(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        client.post(
            "/auth/register",
            json={"username": "casey", "email": "casey@example.com", "password": VALID_PASSWORD},
        )
        response = client.post(
            "/auth/login",
            json={"identifier": "casey", "password": "WrongPassword1!"},
        )

    assert response.status_code == 401


def test_status_endpoint_contracts(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        register_response = client.post(
            "/auth/register",
            json={"username": "casey", "email": "casey@example.com", "password": VALID_PASSWORD},
        )
        token = register_response.json()["access_token"]
        reset_response = client.post(
            "/auth/password-reset/request",
            json={"email": "missing@example.com"},
        )
        confirm_response = client.post(
            "/auth/password-reset/confirm",
            json={"token": "missing", "password": VALID_PASSWORD},
        )
        mfa_response = client.get(
            "/auth/mfa/status",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert reset_response.status_code == 200
    assert reset_response.json() == {"status": "ok"}
    assert confirm_response.status_code == 422
    assert mfa_response.status_code == 200
    assert mfa_response.json() == {"enabled": False, "pending": False}


def _assert_token_response_shape(body: dict[str, object]) -> None:
    assert set(body) == {"access_token", "token_type", "expires_in", "user"}
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert isinstance(body["expires_in"], int)
    user = body["user"]
    assert isinstance(user, dict)
    assert set(user) == {"user_id", "username", "email", "tenant_id", "roles"}
    assert isinstance(UUID(str(user["user_id"])), UUID)
    assert isinstance(UUID(str(user["tenant_id"])), UUID)
    assert user["username"] != user["user_id"]
    assert isinstance(user["roles"], list)
    assert all(isinstance(role, str) for role in user["roles"])
