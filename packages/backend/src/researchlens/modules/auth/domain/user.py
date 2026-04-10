from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, TypeAdapter

from researchlens.shared.errors import ValidationError

MAX_USERNAME_LENGTH = 80
_EMAIL_ADAPTER = TypeAdapter(EmailStr)


def normalize_username(username: str) -> str:
    normalized = username.strip().lower()
    if not normalized:
        raise ValidationError("Username is required.")
    if len(normalized) > MAX_USERNAME_LENGTH:
        raise ValidationError("Username must be 80 characters or fewer.")
    if not all(character.isalnum() or character in {"_", "-", "."} for character in normalized):
        raise ValidationError(
            "Username may only contain letters, numbers, dots, hyphens, and underscores."
        )
    return normalized


def normalize_email(email: str) -> str:
    normalized = str(_EMAIL_ADAPTER.validate_python(email.strip())).lower()
    if not normalized:
        raise ValidationError("Email is required.")
    return normalized


def normalize_roles(roles: list[str]) -> list[str]:
    normalized = sorted({role.strip().lower() for role in roles if role.strip()})
    if not normalized:
        raise ValidationError("At least one role is required.")
    return normalized


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    tenant_id: UUID
    username: str
    email: str
    roles: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        id: UUID,
        tenant_id: UUID,
        username: str,
        email: str,
        roles: list[str],
        created_at: datetime,
        updated_at: datetime,
    ) -> "User":
        return cls(
            id=id,
            tenant_id=tenant_id,
            username=normalize_username(username),
            email=normalize_email(email),
            roles=normalize_roles(roles),
            is_active=True,
            created_at=created_at,
            updated_at=updated_at,
        )

    def require_active(self) -> None:
        if not self.is_active:
            raise ValidationError("User is inactive.")

    def with_password_updated(self, *, updated_at: datetime) -> "User":
        return replace(self, updated_at=updated_at)
