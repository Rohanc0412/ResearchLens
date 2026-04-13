from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from researchlens.shared.db import Base


class RepairPassRow(Base):
    __tablename__ = "repair_passes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "run_id", "pass_index"),
        Index("ix_repair_passes_tenant_run", "tenant_id", "run_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pass_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    selected_section_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    changed_section_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    unresolved_section_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    skipped_section_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RepairResultRow(Base):
    __tablename__ = "repair_results"
    __table_args__ = (
        UniqueConstraint("tenant_id", "repair_pass_id", "section_id"),
        Index("ix_repair_results_tenant_run", "tenant_id", "run_id"),
        Index("ix_repair_results_run_section", "tenant_id", "run_id", "section_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    repair_pass_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("repair_passes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    evaluation_section_result_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("evaluation_section_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    evaluation_pass_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    section_id: Mapped[str] = mapped_column(String(120), nullable=False)
    section_title: Mapped[str] = mapped_column(String(240), nullable=False)
    section_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    changed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    issue_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    original_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    revised_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    revised_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_summary_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    unresolved_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reevaluation_pass_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RepairFallbackEditRow(Base):
    __tablename__ = "repair_fallback_edits"
    __table_args__ = (Index("ix_repair_fallback_edits_result", "repair_result_id"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    repair_result_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("repair_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    edit_kind: Mapped[str] = mapped_column(String(40), nullable=False)
    before_text: Mapped[str] = mapped_column(Text, nullable=False)
    after_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
