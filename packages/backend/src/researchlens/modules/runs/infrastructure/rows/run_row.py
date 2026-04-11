from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from researchlens.shared.db import Base


class RunRow(Base):
    __tablename__ = "runs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "conversation_id", "client_request_id"),
        Index("ix_runs_tenant_project_created", "tenant_id", "project_id", "created_at"),
        Index("ix_runs_tenant_status_updated", "tenant_id", "status", "updated_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    project_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_user_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    current_stage: Mapped[str | None] = mapped_column(String(32), nullable=True)
    output_type: Mapped[str] = mapped_column(String(64), nullable=False)
    trigger_message_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    client_request_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cancel_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    failure_reason: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_event_number: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
