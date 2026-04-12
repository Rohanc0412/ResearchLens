from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from researchlens.shared.db import Base


class DraftingSectionRow(Base):
    __tablename__ = "drafting_sections"
    __table_args__ = (
        UniqueConstraint("run_id", "section_id"),
        UniqueConstraint("run_id", "section_order"),
        Index("ix_drafting_sections_run_order", "run_id", "section_order"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_id: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    section_order: Mapped[int] = mapped_column(Integer, nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    key_points_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DraftingSectionEvidenceRow(Base):
    __tablename__ = "drafting_section_evidence"
    __table_args__ = (
        UniqueConstraint("section_row_id", "chunk_id"),
        Index(
            "ix_drafting_section_evidence_section",
            "section_row_id",
            "source_rank",
            "chunk_index",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    section_row_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("drafting_sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    chunk_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    source_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    source_title: Mapped[str] = mapped_column(String(240), nullable=False)
    excerpt_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DraftingSectionDraftRow(Base):
    __tablename__ = "drafting_section_drafts"
    __table_args__ = (
        UniqueConstraint("run_id", "section_id"),
        Index("ix_drafting_section_drafts_run_order", "run_id", "section_order"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_id: Mapped[str] = mapped_column(String(120), nullable=False)
    section_order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    section_text: Mapped[str] = mapped_column(Text, nullable=False)
    section_summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(80), nullable=False)
    model_name: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DraftingReportDraftRow(Base):
    __tablename__ = "drafting_report_drafts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    markdown_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
