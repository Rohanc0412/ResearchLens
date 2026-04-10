from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from researchlens.shared.db import normalize_migration_database_url
from researchlens_api.create_app import create_app

COOKIE_NAME = "researchlens_refresh"
VALID_PASSWORD = "CorrectHorse1!"


def test_refresh_rotation_invalidates_old_refresh_token(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        client.post(
            "/auth/register",
            json={"username": "casey", "email": "casey@example.com", "password": VALID_PASSWORD},
        )
        old_cookie = client.cookies.get(COOKIE_NAME)
        refresh_response = client.post("/auth/refresh")
        new_cookie = client.cookies.get(COOKIE_NAME)
        assert old_cookie is not None
        client.cookies.set(COOKIE_NAME, old_cookie)
        reused_response = client.post("/auth/refresh")

    assert refresh_response.status_code == 200
    assert old_cookie
    assert new_cookie
    assert new_cookie != old_cookie
    assert reused_response.status_code == 401


def test_logout_revokes_current_refresh_token(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        client.post(
            "/auth/register",
            json={"username": "casey", "email": "casey@example.com", "password": VALID_PASSWORD},
        )
        refresh_token = client.cookies.get(COOKIE_NAME)
        logout_response = client.post("/auth/logout")
        assert refresh_token is not None
        client.cookies.set(COOKIE_NAME, refresh_token)
        refresh_response = client.post("/auth/refresh")

    assert logout_response.status_code == 200
    assert logout_response.json() == {"status": "ok"}
    assert refresh_response.status_code == 401


def test_password_reset_confirm_lifecycle(migrated_database_url: str) -> None:
    app = create_app()
    with TestClient(app) as client:
        register_response = client.post(
            "/auth/register",
            json={"username": "casey", "email": "casey@example.com", "password": VALID_PASSWORD},
        )
        old_refresh_token = client.cookies.get(COOKIE_NAME)
        reset_request = client.post(
            "/auth/password-reset/request",
            json={"email": "casey@example.com"},
        )
        reset_token = app.state.bootstrap.auth_runtime.password_reset_mailer.sent_messages[-1].token
        weak_confirm = client.post(
            "/auth/password-reset/confirm",
            json={"token": reset_token, "password": "weak"},
        )
        valid_confirm = client.post(
            "/auth/password-reset/confirm",
            json={"token": reset_token, "password": "BetterHorse1!"},
        )
        reused_confirm = client.post(
            "/auth/password-reset/confirm",
            json={"token": reset_token, "password": "AnotherHorse1!"},
        )
        assert old_refresh_token is not None
        client.cookies.set(COOKIE_NAME, old_refresh_token)
        old_refresh = client.post("/auth/refresh")
        login_new_password = client.post(
            "/auth/login",
            json={"identifier": "casey", "password": "BetterHorse1!"},
        )

    assert register_response.status_code == 201
    assert reset_request.status_code == 200
    assert reset_request.json() == {"status": "ok"}
    assert weak_confirm.status_code == 422
    assert valid_confirm.status_code == 200
    assert valid_confirm.json() == {"status": "ok"}
    assert reused_confirm.status_code == 422
    assert old_refresh.status_code == 401
    assert login_new_password.status_code == 200


def test_password_reset_confirm_rejects_invalid_and_expired_tokens(
    migrated_database_url: str,
) -> None:
    app = create_app()
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"username": "casey", "email": "casey@example.com", "password": VALID_PASSWORD},
        )
        invalid = client.post(
            "/auth/password-reset/confirm",
            json={"token": "missing", "password": "BetterHorse1!"},
        )
        client.post(
            "/auth/password-reset/request",
            json={"email": "casey@example.com"},
        )
        reset_token = app.state.bootstrap.auth_runtime.password_reset_mailer.sent_messages[-1].token
        _expire_reset_tokens(migrated_database_url)
        expired = client.post(
            "/auth/password-reset/confirm",
            json={"token": reset_token, "password": "BetterHorse1!"},
        )

    assert invalid.status_code == 422
    assert expired.status_code == 422


def test_expired_refresh_token_fails(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        client.post(
            "/auth/register",
            json={"username": "casey", "email": "casey@example.com", "password": VALID_PASSWORD},
        )
        refresh_token = client.cookies.get(COOKIE_NAME)
        _expire_refresh_tokens(migrated_database_url)
        assert refresh_token is not None
        client.cookies.set(COOKIE_NAME, refresh_token)
        response = client.post("/auth/refresh")

    assert response.status_code == 401


def _expire_reset_tokens(database_url: str) -> None:
    engine = create_engine(normalize_migration_database_url(database_url))
    with engine.begin() as connection:
        connection.execute(
            text("update auth_password_resets set expires_at = :expires_at"),
            {"expires_at": "2000-01-01 00:00:00.000000"},
        )


def _expire_refresh_tokens(database_url: str) -> None:
    engine = create_engine(normalize_migration_database_url(database_url))
    with engine.begin() as connection:
        connection.execute(
            text("update auth_refresh_tokens set expires_at = :expires_at"),
            {"expires_at": "2000-01-01 00:00:00.000000"},
        )
