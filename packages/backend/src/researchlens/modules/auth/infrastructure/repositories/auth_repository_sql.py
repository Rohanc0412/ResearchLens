from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.auth.application.ports import AuthRepository, UserCredentials
from researchlens.modules.auth.domain import (
    PasswordResetToken,
    RefreshToken,
    Session,
    User,
)
from researchlens.modules.auth.infrastructure.repositories.auth_mfa_repository_sql import (
    SqlAlchemyMfaRepositoryMixin,
)
from researchlens.modules.auth.infrastructure.repositories.auth_row_mappers import (
    password_reset_from_row,
    refresh_token_from_row,
    session_from_row,
    user_from_row,
)
from researchlens.modules.auth.infrastructure.rows import (
    AuthPasswordResetRow,
    AuthRefreshTokenRow,
    AuthSessionRow,
    AuthUserRow,
)


class SqlAlchemyAuthRepository(SqlAlchemyMfaRepositoryMixin, AuthRepository):
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
        return user_from_row(row)

    async def get_user_by_id(self, *, user_id: UUID) -> User | None:
        row = await self._session.get(AuthUserRow, user_id)
        return user_from_row(row) if row else None

    async def get_user_by_username(self, *, username: str) -> User | None:
        row = await self._session.scalar(
            select(AuthUserRow).where(AuthUserRow.username == username)
        )
        return user_from_row(row) if row else None

    async def get_user_by_email(self, *, email: str) -> User | None:
        row = await self._session.scalar(select(AuthUserRow).where(AuthUserRow.email == email))
        return user_from_row(row) if row else None

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
        return UserCredentials(user=user_from_row(row), password_hash=row.password_hash)

    async def get_user_credentials_by_id(self, *, user_id: UUID) -> UserCredentials | None:
        row = await self._session.get(AuthUserRow, user_id)
        if row is None:
            return None
        return UserCredentials(user=user_from_row(row), password_hash=row.password_hash)

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
        return session_from_row(row)

    async def get_session(self, *, session_id: UUID) -> Session | None:
        row = await self._session.get(AuthSessionRow, session_id)
        return session_from_row(row) if row else None

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
        return refresh_token_from_row(row)

    async def get_refresh_token_by_hash(self, *, token_hash: str) -> RefreshToken | None:
        row = await self._session.scalar(
            select(AuthRefreshTokenRow).where(AuthRefreshTokenRow.token_hash == token_hash)
        )
        return refresh_token_from_row(row) if row else None

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
        return password_reset_from_row(row)

    async def get_password_reset_token_by_hash(
        self,
        *,
        token_hash: str,
    ) -> PasswordResetToken | None:
        row = await self._session.scalar(
            select(AuthPasswordResetRow).where(AuthPasswordResetRow.token_hash == token_hash)
        )
        return password_reset_from_row(row) if row else None

    async def save_password_reset_token(
        self,
        *,
        password_reset_token: PasswordResetToken,
    ) -> None:
        row = await self._session.get(AuthPasswordResetRow, password_reset_token.id)
        if row is None:
            return
        row.used_at = password_reset_token.used_at
