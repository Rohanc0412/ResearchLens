"""phase 7 drafting persistence

Revision ID: 20260412_0006
Revises: 20260410_0005
Create Date: 2026-04-12 12:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260412_0006"
down_revision: str | None = "20260410_0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "drafting_sections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("section_order", sa.Integer(), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("key_points_json", sa.JSON(), nullable=False),
        sa.Column("evidence_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name=op.f("fk_drafting_sections_run_id_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_drafting_sections")),
        sa.UniqueConstraint("run_id", "section_id", name=op.f("uq_drafting_sections_run_id")),
        sa.UniqueConstraint(
            "run_id",
            "section_order",
            name=op.f("uq_drafting_sections_run_id_1"),
        ),
    )
    op.create_index(
        op.f("ix_drafting_sections_run_id"),
        "drafting_sections",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_drafting_sections_tenant_id"),
        "drafting_sections",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_drafting_sections_run_order",
        "drafting_sections",
        ["run_id", "section_order"],
        unique=False,
    )

    op.create_table(
        "drafting_section_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("section_row_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_id", sa.Uuid(), nullable=False),
        sa.Column("source_rank", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("source_title", sa.String(length=240), nullable=False),
        sa.Column("excerpt_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name=op.f("fk_drafting_section_evidence_run_id_runs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["section_row_id"],
            ["drafting_sections.id"],
            name=op.f("fk_drafting_section_evidence_section_row_id_drafting_sections"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_drafting_section_evidence")),
        sa.UniqueConstraint(
            "section_row_id",
            "chunk_id",
            name=op.f("uq_drafting_section_evidence_section_row_id"),
        ),
    )
    op.create_index(
        op.f("ix_drafting_section_evidence_chunk_id"),
        "drafting_section_evidence",
        ["chunk_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_drafting_section_evidence_run_id"),
        "drafting_section_evidence",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_drafting_section_evidence_section_row_id"),
        "drafting_section_evidence",
        ["section_row_id"],
        unique=False,
    )
    op.create_index(
        "ix_drafting_section_evidence_section",
        "drafting_section_evidence",
        ["section_row_id", "source_rank", "chunk_index"],
        unique=False,
    )
    op.create_index(
        op.f("ix_drafting_section_evidence_source_id"),
        "drafting_section_evidence",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_drafting_section_evidence_tenant_id"),
        "drafting_section_evidence",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "drafting_section_drafts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.String(length=120), nullable=False),
        sa.Column("section_order", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("section_text", sa.Text(), nullable=False),
        sa.Column("section_summary", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("provider_name", sa.String(length=80), nullable=False),
        sa.Column("model_name", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name=op.f("fk_drafting_section_drafts_run_id_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_drafting_section_drafts")),
        sa.UniqueConstraint(
            "run_id",
            "section_id",
            name=op.f("uq_drafting_section_drafts_run_id"),
        ),
    )
    op.create_index(
        op.f("ix_drafting_section_drafts_run_id"),
        "drafting_section_drafts",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        "ix_drafting_section_drafts_run_order",
        "drafting_section_drafts",
        ["run_id", "section_order"],
        unique=False,
    )
    op.create_index(
        op.f("ix_drafting_section_drafts_tenant_id"),
        "drafting_section_drafts",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "drafting_report_drafts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("markdown_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name=op.f("fk_drafting_report_drafts_run_id_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_drafting_report_drafts")),
        sa.UniqueConstraint("run_id", name=op.f("uq_drafting_report_drafts_run_id")),
    )
    op.create_index(
        op.f("ix_drafting_report_drafts_run_id"),
        "drafting_report_drafts",
        ["run_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_drafting_report_drafts_tenant_id"),
        "drafting_report_drafts",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_drafting_report_drafts_tenant_id"),
        table_name="drafting_report_drafts",
    )
    op.drop_index(
        op.f("ix_drafting_report_drafts_run_id"),
        table_name="drafting_report_drafts",
    )
    op.drop_table("drafting_report_drafts")
    op.drop_index(
        op.f("ix_drafting_section_drafts_tenant_id"),
        table_name="drafting_section_drafts",
    )
    op.drop_index("ix_drafting_section_drafts_run_order", table_name="drafting_section_drafts")
    op.drop_index(
        op.f("ix_drafting_section_drafts_run_id"),
        table_name="drafting_section_drafts",
    )
    op.drop_table("drafting_section_drafts")
    op.drop_index(
        op.f("ix_drafting_section_evidence_tenant_id"),
        table_name="drafting_section_evidence",
    )
    op.drop_index(
        op.f("ix_drafting_section_evidence_source_id"),
        table_name="drafting_section_evidence",
    )
    op.drop_index(
        "ix_drafting_section_evidence_section",
        table_name="drafting_section_evidence",
    )
    op.drop_index(
        op.f("ix_drafting_section_evidence_section_row_id"),
        table_name="drafting_section_evidence",
    )
    op.drop_index(
        op.f("ix_drafting_section_evidence_run_id"),
        table_name="drafting_section_evidence",
    )
    op.drop_index(
        op.f("ix_drafting_section_evidence_chunk_id"),
        table_name="drafting_section_evidence",
    )
    op.drop_table("drafting_section_evidence")
    op.drop_index("ix_drafting_sections_run_order", table_name="drafting_sections")
    op.drop_index(op.f("ix_drafting_sections_tenant_id"), table_name="drafting_sections")
    op.drop_index(op.f("ix_drafting_sections_run_id"), table_name="drafting_sections")
    op.drop_table("drafting_sections")
