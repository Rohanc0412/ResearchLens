from datetime import UTC, datetime
from uuid import uuid4

import pytest

from researchlens.modules.auth.domain import User
from researchlens.modules.auth.infrastructure.security import (
    BcryptPasswordHasher,
    HmacTokenHasher,
    JwtTokenService,
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
