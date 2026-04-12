from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
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


class EvaluationPassRow(Base):
    __tablename__ = "evaluation_passes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "run_id", "scope", "pass_index"),
        Index("ix_evaluation_passes_tenant_run", "tenant_id", "run_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scope: Mapped[str] = mapped_column(String(40), nullable=False)
    pass_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    section_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evaluated_section_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    issue_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sections_requiring_repair_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quality_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    unsupported_claim_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pass_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ragas_faithfulness_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    issues_by_type_json: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EvaluationSectionResultRow(Base):
    __tablename__ = "evaluation_section_results"
    __table_args__ = (
        UniqueConstraint("tenant_id", "evaluation_pass_id", "section_id"),
        Index("ix_evaluation_section_results_tenant_run", "tenant_id", "run_id"),
        Index("ix_evaluation_section_results_pass", "tenant_id", "evaluation_pass_id"),
        Index("ix_evaluation_section_results_run_section", "tenant_id", "run_id", "section_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    evaluation_pass_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("evaluation_passes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_id: Mapped[str] = mapped_column(String(120), nullable=False)
    section_title: Mapped[str] = mapped_column(String(240), nullable=False)
    section_order: Mapped[int] = mapped_column(Integer, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    claim_count: Mapped[int] = mapped_column(Integer, nullable=False)
    issue_count: Mapped[int] = mapped_column(Integer, nullable=False)
    unsupported_claim_rate: Mapped[float] = mapped_column(Float, nullable=False)
    ragas_faithfulness_pct: Mapped[float] = mapped_column(Float, nullable=False)
    section_has_contradicted_claim: Mapped[bool] = mapped_column(Boolean, nullable=False)
    repair_recommended: Mapped[bool] = mapped_column(Boolean, nullable=False)
    repair_attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EvaluationClaimRow(Base):
    __tablename__ = "evaluation_claims"
    __table_args__ = (
        UniqueConstraint("tenant_id", "evaluation_pass_id", "section_id", "claim_index"),
        Index("ix_evaluation_claims_tenant_run", "tenant_id", "run_id"),
        Index("ix_evaluation_claims_pass", "tenant_id", "evaluation_pass_id"),
        Index("ix_evaluation_claims_run_section", "tenant_id", "run_id", "section_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    evaluation_pass_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("evaluation_passes.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_id: Mapped[str] = mapped_column(String(120), nullable=False)
    section_title: Mapped[str] = mapped_column(String(240), nullable=False)
    section_order: Mapped[int] = mapped_column(Integer, nullable=False)
    claim_index: Mapped[int] = mapped_column(Integer, nullable=False)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EvaluationIssueRow(Base):
    __tablename__ = "evaluation_issues"
    __table_args__ = (
        Index("ix_evaluation_issues_tenant_run", "tenant_id", "run_id"),
        Index("ix_evaluation_issues_pass", "tenant_id", "evaluation_pass_id"),
        Index("ix_evaluation_issues_run_section", "tenant_id", "run_id", "section_id"),
        Index("ix_evaluation_issues_run_type", "tenant_id", "run_id", "issue_type"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    evaluation_pass_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("evaluation_passes.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_result_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("evaluation_section_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    claim_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("evaluation_claims.id", ondelete="CASCADE"),
        nullable=True,
    )
    section_id: Mapped[str] = mapped_column(String(120), nullable=False)
    section_title: Mapped[str] = mapped_column(String(240), nullable=False)
    section_order: Mapped[int] = mapped_column(Integer, nullable=False)
    claim_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    claim_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    issue_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    verdict: Mapped[str | None] = mapped_column(String(40), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    cited_chunk_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    supported_chunk_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    allowed_chunk_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    repair_hint: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
