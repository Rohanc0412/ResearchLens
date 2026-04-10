from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from researchlens.modules.auth.domain import User


class AuthenticatedUserDto(BaseModel):
    user_id: str
    username: str
    email: str
    tenant_id: str
    roles: list[str]

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_user(cls, user: User) -> "AuthenticatedUserDto":
        return cls(
            user_id=str(user.id),
            username=user.username,
            email=user.email,
            tenant_id=str(user.tenant_id),
            roles=list(user.roles),
        )


class AuthTokenResponseDto(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: AuthenticatedUserDto

    model_config = ConfigDict(extra="forbid")


class AuthMfaChallengeResponseDto(BaseModel):
    mfa_required: Literal[True] = True
    mfa_token: str
    user: AuthenticatedUserDto

    model_config = ConfigDict(extra="forbid")


class LogoutResponseDto(BaseModel):
    status: Literal["ok"] = "ok"

    model_config = ConfigDict(extra="forbid")


class PasswordResetRequestResponseDto(BaseModel):
    status: Literal["ok"] = "ok"

    model_config = ConfigDict(extra="forbid")


class PasswordResetConfirmResponseDto(BaseModel):
    status: Literal["ok"] = "ok"

    model_config = ConfigDict(extra="forbid")


class MfaStatusResponseDto(BaseModel):
    enabled: bool
    pending: bool

    model_config = ConfigDict(extra="forbid")


class MfaEnrollStartResponseDto(BaseModel):
    secret: str
    otpauth_uri: str
    issuer: str
    account_name: str
    period: int
    digits: int

    model_config = ConfigDict(extra="forbid")


class MfaEnabledResponseDto(BaseModel):
    enabled: bool

    model_config = ConfigDict(extra="forbid")


@dataclass(frozen=True, slots=True)
class AuthTokenResult:
    response: AuthTokenResponseDto
    refresh_token: str
    refresh_expires_at: datetime


@dataclass(frozen=True, slots=True)
class MfaChallengeResult:
    response: AuthMfaChallengeResponseDto


@dataclass(frozen=True, slots=True)
class AuthenticatedActor:
    user_id: UUID
    tenant_id: UUID
    roles: list[str]
