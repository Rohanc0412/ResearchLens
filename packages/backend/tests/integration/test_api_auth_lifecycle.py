import pyotp
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


def test_totp_mfa_lifecycle(migrated_database_url: str) -> None:
    with TestClient(create_app()) as client:
        register_response = client.post(
            "/auth/register",
            json={"username": "casey", "email": "casey@example.com", "password": VALID_PASSWORD},
        )
        access_token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        start_response = client.post("/auth/mfa/enroll/start", headers=headers)
        secret = start_response.json()["secret"]
        pending_status = client.get("/auth/mfa/status", headers=headers)
        invalid_verify = client.post(
            "/auth/mfa/enroll/verify",
            json={"code": "000000"},
            headers=headers,
        )
        valid_code = pyotp.TOTP(secret).now()
        verify_response = client.post(
            "/auth/mfa/enroll/verify",
            json={"code": valid_code},
            headers=headers,
        )
        enabled_status = client.get("/auth/mfa/status", headers=headers)
        login_response = client.post(
            "/auth/login",
            json={"identifier": "casey", "password": VALID_PASSWORD},
        )
        mfa_token = login_response.json()["mfa_token"]
        invalid_challenge = client.post(
            "/auth/mfa/verify",
            json={"mfa_token": mfa_token, "code": "000000"},
        )
        valid_challenge = client.post(
            "/auth/mfa/verify",
            json={"mfa_token": mfa_token, "code": pyotp.TOTP(secret).now()},
        )
        disable_response = client.post(
            "/auth/mfa/disable",
            json={"code": pyotp.TOTP(secret).now()},
            headers=headers,
        )
        disabled_status = client.get("/auth/mfa/status", headers=headers)
        login_after_disable = client.post(
            "/auth/login",
            json={"identifier": "casey", "password": VALID_PASSWORD},
        )

    assert register_response.status_code == 201
    assert start_response.status_code == 200
    assert pending_status.json() == {"enabled": False, "pending": True}
    assert invalid_verify.status_code == 422
    assert verify_response.status_code == 200
    assert verify_response.json() == {"enabled": True}
    assert enabled_status.json() == {"enabled": True, "pending": False}
    assert login_response.status_code == 200
    assert "access_token" not in login_response.json()
    assert login_response.cookies.get(COOKIE_NAME) is None
    assert invalid_challenge.status_code == 401
    assert valid_challenge.status_code == 200
    assert valid_challenge.cookies.get(COOKIE_NAME)
    assert disable_response.status_code == 200
    assert disable_response.json() == {"enabled": False}
    assert disabled_status.json() == {"enabled": False, "pending": False}
    assert login_after_disable.status_code == 200
    assert "access_token" in login_after_disable.json()


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
