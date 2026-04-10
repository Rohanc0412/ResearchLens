from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from researchlens.shared.errors import AuthenticationError


@dataclass(frozen=True, slots=True)
class RefreshToken:
    id: UUID
    session_id: UUID
    user_id: UUID
    tenant_id: UUID
    token_hash: str
    created_at: datetime
    expires_at: datetime
    rotated_from_id: UUID | None = None
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None

    def require_usable(self, *, now: datetime) -> None:
        if self.revoked_at is not None:
            raise AuthenticationError("Refresh token has been revoked.")
        if self.expires_at <= now:
            raise AuthenticationError("Refresh token has expired.")

    def mark_used(self, *, used_at: datetime) -> "RefreshToken":
        self.require_usable(now=used_at)
        return replace(self, last_used_at=used_at)

    def revoke(self, *, revoked_at: datetime) -> "RefreshToken":
        if self.revoked_at is not None:
            return self
        return replace(self, revoked_at=revoked_at)
