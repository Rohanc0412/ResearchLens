from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from researchlens.shared.db import Base


class AuthMfaFactorRow(Base):
    __tablename__ = "auth_mfa_factors"
    __table_args__ = (
        UniqueConstraint("user_id", "factor_type"),
        Index("ix_auth_mfa_factors_tenant_id", "tenant_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    factor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    enabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
