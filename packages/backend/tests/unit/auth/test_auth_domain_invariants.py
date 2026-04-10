from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from researchlens.modules.auth.domain import PasswordResetToken, RefreshToken, Session
from researchlens.shared.errors import AuthenticationError, ValidationError


def test_session_revocation_blocks_reuse() -> None:
    now = datetime.now(UTC)
    session = Session(
        id=uuid4(),
        user_id=uuid4(),
        tenant_id=uuid4(),
        created_at=now,
        expires_at=now + timedelta(days=1),
    ).revoke(revoked_at=now)

    with pytest.raises(AuthenticationError):
        session.require_usable(now=now)


def test_refresh_token_expiry_blocks_reuse() -> None:
    now = datetime.now(UTC)
    refresh_token = RefreshToken(
        id=uuid4(),
        session_id=uuid4(),
        user_id=uuid4(),
        tenant_id=uuid4(),
        token_hash="hashed",
        created_at=now - timedelta(days=2),
        expires_at=now - timedelta(days=1),
    )

    with pytest.raises(AuthenticationError):
        refresh_token.require_usable(now=now)


def test_password_reset_token_is_one_time_use() -> None:
    now = datetime.now(UTC)
    reset_token = PasswordResetToken(
        id=uuid4(),
        user_id=uuid4(),
        tenant_id=uuid4(),
        token_hash="hashed",
        created_at=now,
        expires_at=now + timedelta(minutes=30),
    ).mark_used(used_at=now)

    with pytest.raises(ValidationError):
        reset_token.require_usable(now=now)
