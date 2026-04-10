from datetime import UTC, datetime
from uuid import uuid4

import pyotp
import pytest

from researchlens.modules.auth.domain import User
from researchlens.modules.auth.infrastructure.security import (
    BcryptPasswordHasher,
    HmacTokenHasher,
    JwtTokenService,
    PyotpTotpService,
)
from researchlens.shared.errors import AuthenticationError


def test_password_hasher_hashes_and_verifies_passwords() -> None:
    hasher = BcryptPasswordHasher()

    password_hash = hasher.hash_password("CorrectHorse1!")

    assert password_hash != "CorrectHorse1!"
    assert hasher.verify_password("CorrectHorse1!", password_hash)
    assert not hasher.verify_password("WrongPassword1!", password_hash)


def test_hmac_token_hasher_is_stable_and_secret_scoped() -> None:
    first = HmacTokenHasher(secret="one")
    second = HmacTokenHasher(secret="two")

    assert first.hash_token("raw-token") == first.hash_token("raw-token")
    assert first.hash_token("raw-token") != second.hash_token("raw-token")


def test_access_token_issue_and_verify_round_trip() -> None:
    now = datetime.now(UTC)
    user = User.create(
        id=uuid4(),
        tenant_id=uuid4(),
        username="casey",
        email="casey@example.com",
        roles=["owner"],
        created_at=now,
        updated_at=now,
    )
    session_id = uuid4()
    service = JwtTokenService(
        secret="unit-test-access-token-secret-32-bytes",
        issuer="researchlens-test",
        access_token_minutes=15,
        clock_skew_seconds=0,
        mfa_challenge_minutes=5,
    )

    issued = service.issue_access_token(
        user=user,
        session_id=session_id,
        issued_at=now,
    )
    claims = service.verify_access_token(issued.token)

    assert claims.user_id == user.id
    assert claims.tenant_id == user.tenant_id
    assert claims.session_id == session_id
    assert claims.roles == ["owner"]
    assert issued.expires_in == 900


def test_access_token_rejects_wrong_issuer() -> None:
    now = datetime.now(UTC)
    user = User.create(
        id=uuid4(),
        tenant_id=uuid4(),
        username="casey",
        email="casey@example.com",
        roles=["owner"],
        created_at=now,
        updated_at=now,
    )
    issuer = JwtTokenService(
        secret="unit-test-access-token-secret-32-bytes",
        issuer="one",
        access_token_minutes=15,
        clock_skew_seconds=0,
        mfa_challenge_minutes=5,
    )
    verifier = JwtTokenService(
        secret="unit-test-access-token-secret-32-bytes",
        issuer="two",
        access_token_minutes=15,
        clock_skew_seconds=0,
        mfa_challenge_minutes=5,
    )

    issued = issuer.issue_access_token(
        user=user,
        session_id=uuid4(),
        issued_at=now,
    )

    with pytest.raises(AuthenticationError):
        verifier.verify_access_token(issued.token)


def test_mfa_challenge_token_verifies_claims() -> None:
    now = datetime.now(UTC)
    user = User.create(
        id=uuid4(),
        tenant_id=uuid4(),
        username="casey",
        email="casey@example.com",
        roles=["owner"],
        created_at=now,
        updated_at=now,
    )
    service = JwtTokenService(
        secret="unit-test-access-token-secret-32-bytes",
        issuer="researchlens-test",
        access_token_minutes=15,
        clock_skew_seconds=0,
        mfa_challenge_minutes=5,
    )

    token = service.issue_mfa_challenge(user=user, issued_at=now)
    claims = service.verify_mfa_challenge(token)

    assert claims.user_id == user.id
    assert claims.tenant_id == user.tenant_id
    assert claims.roles == ["owner"]
    assert claims.session_id is None


def test_totp_service_generates_uri_and_verifies_code() -> None:
    now = datetime.now(UTC)
    service = PyotpTotpService(
        issuer="ResearchLens",
        period_seconds=30,
        digits=6,
        window=1,
    )
    secret = service.generate_secret()
    uri = service.provisioning_uri(secret=secret, account_name="casey@example.com")
    code = pyotp.TOTP(secret).at(now)

    assert uri.startswith("otpauth://totp/ResearchLens:casey%40example.com")
    assert service.verify_code(secret=secret, code=code, verified_at=now)
    assert not service.verify_code(secret=secret, code="000000", verified_at=now)
