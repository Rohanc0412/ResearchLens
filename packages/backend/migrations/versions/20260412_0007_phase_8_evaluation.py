"""phase 8 evaluation persistence

Revision ID: 20260412_0007
Revises: 20260412_0006
Create Date: 2026-04-12 18:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260412_0007"
down_revision: str | None = "20260412_0006"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evaluation_passes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("scope", sa.String(length=40), nullable=False),
        sa.Column("pass_index", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("section_count", sa.Integer(), nullable=False),
        sa.Column("evaluated_section_count", sa.Integer(), nullable=False),
        sa.Column("issue_count", sa.Integer(), nullable=False),
        sa.Column("sections_requiring_repair_count", sa.Integer(), nullable=False),
        sa.Column("quality_pct", sa.Float(), nullable=False),
        sa.Column("unsupported_claim_rate", sa.Float(), nullable=False),
        sa.Column("pass_rate", sa.Float(), nullable=False),
        sa.Column("ragas_faithfulness_pct", sa.Float(), nullable=False),
        sa.Column("issues_by_type_json", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "run_id", "scope", "pass_index"),
    )
    op.create_index("ix_evaluation_passes_tenant_run", "evaluation_passes", ["tenant_id", "run_id"])
    op.create_index(op.f("ix_evaluation_passes_run_id"), "evaluation_passes", ["run_id"])
    op.create_index(op.f("ix_evaluation_passes_tenant_id"), "evaluation_passes", ["tenant_id"])

    op.create_table(
        "evaluation_section_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_pass_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.String(length=120), nullable=False),
        sa.Column("section_title", sa.String(length=240), nullable=False),
        sa.Column("section_order", sa.Integer(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("claim_count", sa.Integer(), nullable=False),
        sa.Column("issue_count", sa.Integer(), nullable=False),
        sa.Column("unsupported_claim_rate", sa.Float(), nullable=False),
        sa.Column("ragas_faithfulness_pct", sa.Float(), nullable=False),
        sa.Column("section_has_contradicted_claim", sa.Boolean(), nullable=False),
        sa.Column("repair_recommended", sa.Boolean(), nullable=False),
        sa.Column("repair_attempt_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["evaluation_pass_id"],
            ["evaluation_passes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "evaluation_pass_id", "section_id"),
    )
    op.create_index(
        "ix_evaluation_section_results_tenant_run",
        "evaluation_section_results",
        ["tenant_id", "run_id"],
    )
    op.create_index(
        "ix_evaluation_section_results_pass",
        "evaluation_section_results",
        ["tenant_id", "evaluation_pass_id"],
    )
    op.create_index(
        "ix_evaluation_section_results_run_section",
        "evaluation_section_results",
        ["tenant_id", "run_id", "section_id"],
    )
    op.create_index(
        op.f("ix_evaluation_section_results_evaluation_pass_id"),
        "evaluation_section_results",
        ["evaluation_pass_id"],
    )
    op.create_index(
        op.f("ix_evaluation_section_results_tenant_id"),
        "evaluation_section_results",
        ["tenant_id"],
    )

    op.create_table(
        "evaluation_claims",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_pass_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.String(length=120), nullable=False),
        sa.Column("section_title", sa.String(length=240), nullable=False),
        sa.Column("section_order", sa.Integer(), nullable=False),
        sa.Column("claim_index", sa.Integer(), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["evaluation_pass_id"],
            ["evaluation_passes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "evaluation_pass_id", "section_id", "claim_index"),
    )
    op.create_index("ix_evaluation_claims_tenant_run", "evaluation_claims", ["tenant_id", "run_id"])
    op.create_index(
        "ix_evaluation_claims_pass",
        "evaluation_claims",
        ["tenant_id", "evaluation_pass_id"],
    )
    op.create_index(
        "ix_evaluation_claims_run_section",
        "evaluation_claims",
        ["tenant_id", "run_id", "section_id"],
    )
    op.create_index(op.f("ix_evaluation_claims_tenant_id"), "evaluation_claims", ["tenant_id"])

    op.create_table(
        "evaluation_issues",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_pass_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("section_result_id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=True),
        sa.Column("section_id", sa.String(length=120), nullable=False),
        sa.Column("section_title", sa.String(length=240), nullable=False),
        sa.Column("section_order", sa.Integer(), nullable=False),
        sa.Column("claim_index", sa.Integer(), nullable=True),
        sa.Column("claim_text", sa.Text(), nullable=True),
        sa.Column("issue_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("verdict", sa.String(length=40), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("cited_chunk_ids_json", sa.JSON(), nullable=False),
        sa.Column("supported_chunk_ids_json", sa.JSON(), nullable=False),
        sa.Column("allowed_chunk_ids_json", sa.JSON(), nullable=False),
        sa.Column("repair_hint", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["evaluation_claims.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["evaluation_pass_id"],
            ["evaluation_passes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["section_result_id"],
            ["evaluation_section_results.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evaluation_issues_tenant_run", "evaluation_issues", ["tenant_id", "run_id"])
    op.create_index(
        "ix_evaluation_issues_pass",
        "evaluation_issues",
        ["tenant_id", "evaluation_pass_id"],
    )
    op.create_index(
        "ix_evaluation_issues_run_section",
        "evaluation_issues",
        ["tenant_id", "run_id", "section_id"],
    )
    op.create_index(
        "ix_evaluation_issues_run_type",
        "evaluation_issues",
        ["tenant_id", "run_id", "issue_type"],
    )
    op.create_index(op.f("ix_evaluation_issues_tenant_id"), "evaluation_issues", ["tenant_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_evaluation_issues_tenant_id"), table_name="evaluation_issues")
    op.drop_index("ix_evaluation_issues_run_type", table_name="evaluation_issues")
    op.drop_index("ix_evaluation_issues_run_section", table_name="evaluation_issues")
    op.drop_index("ix_evaluation_issues_pass", table_name="evaluation_issues")
    op.drop_index("ix_evaluation_issues_tenant_run", table_name="evaluation_issues")
    op.drop_table("evaluation_issues")
    op.drop_index(op.f("ix_evaluation_claims_tenant_id"), table_name="evaluation_claims")
    op.drop_index("ix_evaluation_claims_run_section", table_name="evaluation_claims")
    op.drop_index("ix_evaluation_claims_pass", table_name="evaluation_claims")
    op.drop_index("ix_evaluation_claims_tenant_run", table_name="evaluation_claims")
    op.drop_table("evaluation_claims")
    op.drop_index(
        op.f("ix_evaluation_section_results_tenant_id"),
        table_name="evaluation_section_results",
    )
    op.drop_index(
        op.f("ix_evaluation_section_results_evaluation_pass_id"),
        table_name="evaluation_section_results",
    )
    op.drop_index(
        "ix_evaluation_section_results_run_section",
        table_name="evaluation_section_results",
    )
    op.drop_index("ix_evaluation_section_results_pass", table_name="evaluation_section_results")
    op.drop_index(
        "ix_evaluation_section_results_tenant_run",
        table_name="evaluation_section_results",
    )
    op.drop_table("evaluation_section_results")
    op.drop_index(op.f("ix_evaluation_passes_tenant_id"), table_name="evaluation_passes")
    op.drop_index(op.f("ix_evaluation_passes_run_id"), table_name="evaluation_passes")
    op.drop_index("ix_evaluation_passes_tenant_run", table_name="evaluation_passes")
    op.drop_table("evaluation_passes")
