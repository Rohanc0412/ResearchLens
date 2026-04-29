"""phase 11 retrieval outline persistence

Revision ID: 20260419_0010
Revises: 20260413_0009
Create Date: 2026-04-19 16:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260419_0010"
down_revision: str | None = "20260413_0009"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "retrieval_outlines",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("report_title", sa.String(length=240), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name=op.f("fk_retrieval_outlines_run_id_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_retrieval_outlines")),
        sa.UniqueConstraint("run_id", name="uq_retrieval_outlines_run"),
    )
    op.create_index(
        op.f("ix_retrieval_outlines_run_id"),
        "retrieval_outlines",
        ["run_id"],
        unique=False,
    )

    op.create_table(
        "retrieval_outline_sections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("outline_id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("section_order", sa.Integer(), nullable=False),
        sa.Column("key_points_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["outline_id"],
            ["retrieval_outlines.id"],
            name=op.f("fk_retrieval_outline_sections_outline_id_retrieval_outlines"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_retrieval_outline_sections")),
        sa.UniqueConstraint(
            "outline_id",
            "section_id",
            name=op.f("uq_retrieval_outline_sections_outline_id"),
        ),
        sa.UniqueConstraint(
            "outline_id",
            "section_order",
            name="uq_retrieval_outline_sections_outline_order",
        ),
    )
    op.create_index(
        op.f("ix_retrieval_outline_sections_outline_id"),
        "retrieval_outline_sections",
        ["outline_id"],
        unique=False,
    )
    op.create_index(
        "ix_retrieval_outline_sections_outline_order",
        "retrieval_outline_sections",
        ["outline_id", "section_order"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_retrieval_outline_sections_outline_order",
        table_name="retrieval_outline_sections",
    )
    op.drop_index(
        op.f("ix_retrieval_outline_sections_outline_id"),
        table_name="retrieval_outline_sections",
    )
    op.drop_table("retrieval_outline_sections")
    op.drop_index(op.f("ix_retrieval_outlines_run_id"), table_name="retrieval_outlines")
    op.drop_table("retrieval_outlines")
