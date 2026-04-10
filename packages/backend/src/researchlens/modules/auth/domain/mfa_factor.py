from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from researchlens.shared.errors import ValidationError

TOTP_FACTOR_TYPE = "totp"


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

    @classmethod
    def create_totp(
        cls,
        *,
        id: UUID,
        user_id: UUID,
        tenant_id: UUID,
        secret: str,
        created_at: datetime,
    ) -> "MfaFactor":
        if not secret:
            raise ValidationError("MFA secret is required.")
        return cls(
            id=id,
            user_id=user_id,
            tenant_id=tenant_id,
            factor_type=TOTP_FACTOR_TYPE,
            secret=secret,
            created_at=created_at,
        )

    def replace_pending_secret(self, *, secret: str, created_at: datetime) -> "MfaFactor":
        if self.enabled:
            raise ValidationError("Enabled MFA factors cannot be replaced.")
        if not secret:
            raise ValidationError("MFA secret is required.")
        return replace(self, secret=secret, created_at=created_at, last_used_at=None)

    def enable(self, *, enabled_at: datetime) -> "MfaFactor":
        if self.factor_type != TOTP_FACTOR_TYPE:
            raise ValidationError("Unsupported MFA factor type.")
        return replace(self, enabled_at=enabled_at)

    def mark_used(self, *, used_at: datetime) -> "MfaFactor":
        if not self.enabled:
            raise ValidationError("MFA factor is not enabled.")
        return replace(self, last_used_at=used_at)
