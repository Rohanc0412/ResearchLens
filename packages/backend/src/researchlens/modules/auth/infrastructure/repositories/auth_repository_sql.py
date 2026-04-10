from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.auth.application.ports import AuthRepository, UserCredentials
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


class SqlAlchemyAuthRepository(AuthRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_user(self, *, user: User, password_hash: str) -> User:
        row = AuthUserRow(
            id=user.id,
            tenant_id=user.tenant_id,
            username=user.username,
            email=user.email,
            password_hash=password_hash,
            roles=user.roles,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self._session.add(row)
        await self._session.flush()
        return _user_from_row(row)

    async def get_user_by_id(self, *, user_id: UUID) -> User | None:
        row = await self._session.get(AuthUserRow, user_id)
        return _user_from_row(row) if row else None

    async def get_user_by_username(self, *, username: str) -> User | None:
        row = await self._session.scalar(
            select(AuthUserRow).where(AuthUserRow.username == username)
        )
        return _user_from_row(row) if row else None

    async def get_user_by_email(self, *, email: str) -> User | None:
        row = await self._session.scalar(select(AuthUserRow).where(AuthUserRow.email == email))
        return _user_from_row(row) if row else None

    async def get_user_credentials_by_identifier(
        self,
        *,
        identifier: str,
    ) -> UserCredentials | None:
        row = await self._session.scalar(
            select(AuthUserRow).where(
                or_(AuthUserRow.username == identifier, AuthUserRow.email == identifier)
            )
        )
        if row is None:
            return None
        return UserCredentials(user=_user_from_row(row), password_hash=row.password_hash)

    async def update_user_password_hash(
        self,
        *,
        user_id: UUID,
        password_hash: str,
        updated_at: datetime,
    ) -> None:
        await self._session.execute(
            update(AuthUserRow)
            .where(AuthUserRow.id == user_id)
            .values(password_hash=password_hash, updated_at=updated_at)
        )

    async def add_session(self, *, session: Session) -> Session:
        row = AuthSessionRow(
            id=session.id,
            user_id=session.user_id,
            tenant_id=session.tenant_id,
            created_at=session.created_at,
            expires_at=session.expires_at,
            last_used_at=session.last_used_at,
            revoked_at=session.revoked_at,
        )
        self._session.add(row)
        await self._session.flush()
        return _session_from_row(row)

    async def get_session(self, *, session_id: UUID) -> Session | None:
        row = await self._session.get(AuthSessionRow, session_id)
        return _session_from_row(row) if row else None

    async def save_session(self, *, session: Session) -> None:
        row = await self._session.get(AuthSessionRow, session.id)
        if row is None:
            return
        row.last_used_at = session.last_used_at
        row.revoked_at = session.revoked_at
        row.expires_at = session.expires_at

    async def revoke_active_sessions_for_user(self, *, user_id: UUID, revoked_at: datetime) -> None:
        await self._session.execute(
            update(AuthSessionRow)
            .where(AuthSessionRow.user_id == user_id, AuthSessionRow.revoked_at.is_(None))
            .values(revoked_at=revoked_at)
        )

    async def add_refresh_token(self, *, refresh_token: RefreshToken) -> RefreshToken:
        row = AuthRefreshTokenRow(
            id=refresh_token.id,
            session_id=refresh_token.session_id,
            user_id=refresh_token.user_id,
            tenant_id=refresh_token.tenant_id,
            token_hash=refresh_token.token_hash,
            created_at=refresh_token.created_at,
            expires_at=refresh_token.expires_at,
            rotated_from_id=refresh_token.rotated_from_id,
            last_used_at=refresh_token.last_used_at,
            revoked_at=refresh_token.revoked_at,
        )
        self._session.add(row)
        await self._session.flush()
        return _refresh_token_from_row(row)

    async def get_refresh_token_by_hash(self, *, token_hash: str) -> RefreshToken | None:
        row = await self._session.scalar(
            select(AuthRefreshTokenRow).where(AuthRefreshTokenRow.token_hash == token_hash)
        )
        return _refresh_token_from_row(row) if row else None

    async def save_refresh_token(self, *, refresh_token: RefreshToken) -> None:
        row = await self._session.get(AuthRefreshTokenRow, refresh_token.id)
        if row is None:
            return
        row.last_used_at = refresh_token.last_used_at
        row.revoked_at = refresh_token.revoked_at

    async def revoke_active_refresh_tokens_for_user(
        self,
        *,
        user_id: UUID,
        revoked_at: datetime,
    ) -> None:
        await self._session.execute(
            update(AuthRefreshTokenRow)
            .where(AuthRefreshTokenRow.user_id == user_id, AuthRefreshTokenRow.revoked_at.is_(None))
            .values(revoked_at=revoked_at)
        )

    async def add_password_reset_token(
        self,
        *,
        password_reset_token: PasswordResetToken,
    ) -> PasswordResetToken:
        row = AuthPasswordResetRow(
            id=password_reset_token.id,
            user_id=password_reset_token.user_id,
            tenant_id=password_reset_token.tenant_id,
            token_hash=password_reset_token.token_hash,
            created_at=password_reset_token.created_at,
            expires_at=password_reset_token.expires_at,
            used_at=password_reset_token.used_at,
        )
        self._session.add(row)
        await self._session.flush()
        return _password_reset_from_row(row)

    async def get_password_reset_token_by_hash(
        self,
        *,
        token_hash: str,
    ) -> PasswordResetToken | None:
        row = await self._session.scalar(
            select(AuthPasswordResetRow).where(AuthPasswordResetRow.token_hash == token_hash)
        )
        return _password_reset_from_row(row) if row else None

    async def save_password_reset_token(
        self,
        *,
        password_reset_token: PasswordResetToken,
    ) -> None:
        row = await self._session.get(AuthPasswordResetRow, password_reset_token.id)
        if row is None:
            return
        row.used_at = password_reset_token.used_at

    async def get_mfa_factors_for_user(self, *, user_id: UUID) -> list[MfaFactor]:
        rows = await self._session.scalars(
            select(AuthMfaFactorRow).where(AuthMfaFactorRow.user_id == user_id)
        )
        return [_mfa_factor_from_row(row) for row in rows]


def _user_from_row(row: AuthUserRow) -> User:
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


def _session_from_row(row: AuthSessionRow) -> Session:
    return Session(
        id=row.id,
        user_id=row.user_id,
        tenant_id=row.tenant_id,
        created_at=_ensure_aware(row.created_at),
        expires_at=_ensure_aware(row.expires_at),
        last_used_at=_ensure_aware_or_none(row.last_used_at),
        revoked_at=_ensure_aware_or_none(row.revoked_at),
    )


def _refresh_token_from_row(row: AuthRefreshTokenRow) -> RefreshToken:
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


def _password_reset_from_row(row: AuthPasswordResetRow) -> PasswordResetToken:
    return PasswordResetToken(
        id=row.id,
        user_id=row.user_id,
        tenant_id=row.tenant_id,
        token_hash=row.token_hash,
        created_at=_ensure_aware(row.created_at),
        expires_at=_ensure_aware(row.expires_at),
        used_at=_ensure_aware_or_none(row.used_at),
    )


def _mfa_factor_from_row(row: AuthMfaFactorRow) -> MfaFactor:
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
