from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from researchlens.shared.errors import AuthenticationError


@dataclass(frozen=True, slots=True)
class Session:
    id: UUID
    user_id: UUID
    tenant_id: UUID
    created_at: datetime
    expires_at: datetime
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None

    def require_usable(self, *, now: datetime) -> None:
        if self.revoked_at is not None:
            raise AuthenticationError("Session has been revoked.")
        if self.expires_at <= now:
            raise AuthenticationError("Session has expired.")

    def mark_used(self, *, used_at: datetime) -> "Session":
        self.require_usable(now=used_at)
        return replace(self, last_used_at=used_at)

    def revoke(self, *, revoked_at: datetime) -> "Session":
        if self.revoked_at is not None:
            return self
        return replace(self, revoked_at=revoked_at)
