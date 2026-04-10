from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from researchlens.modules.auth.domain import (
    MfaFactor,
    PasswordResetToken,
    RefreshToken,
    Session,
    User,
)


@dataclass(frozen=True, slots=True)
class UserCredentials:
    user: User
    password_hash: str


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    user_id: UUID
    tenant_id: UUID
    roles: list[str]
    session_id: UUID | None


@dataclass(frozen=True, slots=True)
class IssuedAccessToken:
    token: str
    expires_in: int


class TransactionManager(Protocol):
    def boundary(self) -> AbstractAsyncContextManager[None]: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class PasswordHasher(Protocol):
    def hash_password(self, password: str) -> str: ...

    def verify_password(self, password: str, password_hash: str) -> bool: ...


class TokenHasher(Protocol):
    def hash_token(self, token: str) -> str: ...


class OpaqueTokenGenerator(Protocol):
    def generate(self) -> str: ...


class TokenIssuer(Protocol):
    def issue_access_token(
        self,
        *,
        user: User,
        session_id: UUID,
        issued_at: datetime,
    ) -> IssuedAccessToken: ...

    def verify_access_token(self, token: str) -> AccessTokenClaims: ...

    def issue_mfa_challenge(
        self,
        *,
        user: User,
        issued_at: datetime,
    ) -> str: ...


class PasswordResetMailer(Protocol):
    async def send_password_reset(self, *, email: str, token: str) -> None: ...


class AuthRepository(Protocol):
    async def add_user(self, *, user: User, password_hash: str) -> User: ...

    async def get_user_by_id(self, *, user_id: UUID) -> User | None: ...

    async def get_user_by_username(self, *, username: str) -> User | None: ...

    async def get_user_by_email(self, *, email: str) -> User | None: ...

    async def get_user_credentials_by_identifier(
        self,
        *,
        identifier: str,
    ) -> UserCredentials | None: ...

    async def update_user_password_hash(
        self,
        *,
        user_id: UUID,
        password_hash: str,
        updated_at: datetime,
    ) -> None: ...

    async def add_session(self, *, session: Session) -> Session: ...

    async def get_session(self, *, session_id: UUID) -> Session | None: ...

    async def save_session(self, *, session: Session) -> None: ...

    async def revoke_active_sessions_for_user(
        self,
        *,
        user_id: UUID,
        revoked_at: datetime,
    ) -> None: ...

    async def add_refresh_token(self, *, refresh_token: RefreshToken) -> RefreshToken: ...

    async def get_refresh_token_by_hash(self, *, token_hash: str) -> RefreshToken | None: ...

    async def save_refresh_token(self, *, refresh_token: RefreshToken) -> None: ...

    async def revoke_active_refresh_tokens_for_user(
        self,
        *,
        user_id: UUID,
        revoked_at: datetime,
    ) -> None: ...

    async def add_password_reset_token(
        self,
        *,
        password_reset_token: PasswordResetToken,
    ) -> PasswordResetToken: ...

    async def get_password_reset_token_by_hash(
        self,
        *,
        token_hash: str,
    ) -> PasswordResetToken | None: ...

    async def save_password_reset_token(
        self,
        *,
        password_reset_token: PasswordResetToken,
    ) -> None: ...

    async def get_mfa_factors_for_user(self, *, user_id: UUID) -> list[MfaFactor]: ...
