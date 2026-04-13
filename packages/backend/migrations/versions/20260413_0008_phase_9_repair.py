"""phase 9 repair persistence

Revision ID: 20260413_0008
Revises: 20260412_0007
Create Date: 2026-04-13 09:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260413_0008"
down_revision: str | None = "20260412_0007"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "evaluation_section_results",
        sa.Column("repair_result_id", sa.Uuid(), nullable=True),
    )
    op.create_table(
        "repair_passes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("pass_index", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("selected_section_ids_json", sa.JSON(), nullable=False),
        sa.Column("changed_section_ids_json", sa.JSON(), nullable=False),
        sa.Column("unresolved_section_ids_json", sa.JSON(), nullable=False),
        sa.Column("skipped_section_ids_json", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "run_id", "pass_index"),
    )
    op.create_index("ix_repair_passes_tenant_run", "repair_passes", ["tenant_id", "run_id"])
    op.create_index(op.f("ix_repair_passes_run_id"), "repair_passes", ["run_id"])
    op.create_index(op.f("ix_repair_passes_tenant_id"), "repair_passes", ["tenant_id"])

    op.create_table(
        "repair_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("repair_pass_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_section_result_id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_pass_id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.String(length=120), nullable=False),
        sa.Column("section_title", sa.String(length=240), nullable=False),
        sa.Column("section_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("changed", sa.Boolean(), nullable=False),
        sa.Column("issue_ids_json", sa.JSON(), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=True),
        sa.Column("original_summary", sa.Text(), nullable=True),
        sa.Column("revised_text", sa.Text(), nullable=True),
        sa.Column("revised_summary", sa.Text(), nullable=True),
        sa.Column("validation_summary_json", sa.JSON(), nullable=False),
        sa.Column("unresolved_reason", sa.Text(), nullable=True),
        sa.Column("reevaluation_pass_id", sa.Uuid(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["evaluation_section_result_id"],
            ["evaluation_section_results.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["repair_pass_id"], ["repair_passes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "repair_pass_id", "section_id"),
    )
    op.create_index("ix_repair_results_tenant_run", "repair_results", ["tenant_id", "run_id"])
    op.create_index(
        "ix_repair_results_run_section",
        "repair_results",
        ["tenant_id", "run_id", "section_id"],
    )
    op.create_index(op.f("ix_repair_results_repair_pass_id"), "repair_results", ["repair_pass_id"])
    op.create_index(op.f("ix_repair_results_tenant_id"), "repair_results", ["tenant_id"])

    op.create_table(
        "repair_fallback_edits",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("repair_result_id", sa.Uuid(), nullable=False),
        sa.Column("edit_kind", sa.String(length=40), nullable=False),
        sa.Column("before_text", sa.Text(), nullable=False),
        sa.Column("after_text", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["repair_result_id"], ["repair_results.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_repair_fallback_edits_result",
        "repair_fallback_edits",
        ["repair_result_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_repair_fallback_edits_result", table_name="repair_fallback_edits")
    op.drop_table("repair_fallback_edits")
    op.drop_index(op.f("ix_repair_results_tenant_id"), table_name="repair_results")
    op.drop_index(op.f("ix_repair_results_repair_pass_id"), table_name="repair_results")
    op.drop_index("ix_repair_results_run_section", table_name="repair_results")
    op.drop_index("ix_repair_results_tenant_run", table_name="repair_results")
    op.drop_table("repair_results")
    op.drop_index(op.f("ix_repair_passes_tenant_id"), table_name="repair_passes")
    op.drop_index(op.f("ix_repair_passes_run_id"), table_name="repair_passes")
    op.drop_index("ix_repair_passes_tenant_run", table_name="repair_passes")
    op.drop_table("repair_passes")
    op.drop_column("evaluation_section_results", "repair_result_id")
