from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from researchlens.shared.errors import ValidationError


@dataclass(frozen=True, slots=True)
class PasswordResetToken:
    id: UUID
    user_id: UUID
    tenant_id: UUID
    token_hash: str
    created_at: datetime
    expires_at: datetime
    used_at: datetime | None = None

    def require_usable(self, *, now: datetime) -> None:
        if self.used_at is not None:
            raise ValidationError("Password reset token has already been used.")
        if self.expires_at <= now:
            raise ValidationError("Password reset token has expired.")

    def mark_used(self, *, used_at: datetime) -> "PasswordResetToken":
        self.require_usable(now=used_at)
        return replace(self, used_at=used_at)
