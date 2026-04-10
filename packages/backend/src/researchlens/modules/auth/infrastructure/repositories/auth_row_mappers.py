from datetime import UTC, datetime

from researchlens.modules.auth.domain import (
    MfaFactor,
    PasswordResetToken,
    RefreshToken,
    Session,
    User,
)
from researchlens.modules.auth.infrastructure.rows import (
    AuthMfaFactorRow,
    AuthPasswordResetRow,
    AuthRefreshTokenRow,
    AuthSessionRow,
    AuthUserRow,
)


def user_from_row(row: AuthUserRow) -> User:
    return User(
        id=row.id,
        tenant_id=row.tenant_id,
        username=row.username,
        email=row.email,
        roles=list(row.roles),
        is_active=row.is_active,
        created_at=_ensure_aware(row.created_at),
        updated_at=_ensure_aware(row.updated_at),
    )


def session_from_row(row: AuthSessionRow) -> Session:
    return Session(
        id=row.id,
        user_id=row.user_id,
        tenant_id=row.tenant_id,
        created_at=_ensure_aware(row.created_at),
        expires_at=_ensure_aware(row.expires_at),
        last_used_at=_ensure_aware_or_none(row.last_used_at),
        revoked_at=_ensure_aware_or_none(row.revoked_at),
    )


def refresh_token_from_row(row: AuthRefreshTokenRow) -> RefreshToken:
    return RefreshToken(
        id=row.id,
        session_id=row.session_id,
        user_id=row.user_id,
        tenant_id=row.tenant_id,
        token_hash=row.token_hash,
        created_at=_ensure_aware(row.created_at),
        expires_at=_ensure_aware(row.expires_at),
        rotated_from_id=row.rotated_from_id,
        last_used_at=_ensure_aware_or_none(row.last_used_at),
        revoked_at=_ensure_aware_or_none(row.revoked_at),
    )


def password_reset_from_row(row: AuthPasswordResetRow) -> PasswordResetToken:
    return PasswordResetToken(
        id=row.id,
        user_id=row.user_id,
        tenant_id=row.tenant_id,
        token_hash=row.token_hash,
        created_at=_ensure_aware(row.created_at),
        expires_at=_ensure_aware(row.expires_at),
        used_at=_ensure_aware_or_none(row.used_at),
    )


def mfa_factor_from_row(row: AuthMfaFactorRow) -> MfaFactor:
    return MfaFactor(
        id=row.id,
        user_id=row.user_id,
        tenant_id=row.tenant_id,
        factor_type=row.factor_type,
        secret=row.secret,
        created_at=_ensure_aware(row.created_at),
        enabled_at=_ensure_aware_or_none(row.enabled_at),
        last_used_at=_ensure_aware_or_none(row.last_used_at),
    )


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _ensure_aware_or_none(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _ensure_aware(value)
