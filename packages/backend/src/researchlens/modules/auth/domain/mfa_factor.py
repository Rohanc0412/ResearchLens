from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MfaFactor:
    id: UUID
    user_id: UUID
    tenant_id: UUID
    factor_type: str
    secret: str
    created_at: datetime
    enabled_at: datetime | None = None
    last_used_at: datetime | None = None

    @property
    def enabled(self) -> bool:
        return self.enabled_at is not None

    @property
    def pending(self) -> bool:
        return self.enabled_at is None
