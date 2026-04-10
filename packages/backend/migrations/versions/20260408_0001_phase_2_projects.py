"""phase 2 projects slice

Revision ID: 20260408_0001
Revises:
Create Date: 2026-04-08 20:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260408_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
        sa.UniqueConstraint("tenant_id", "name", name=op.f("uq_projects_tenant_id")),
    )
    op.create_index(
        "ix_projects_tenant_id_updated_at_created_at",
        "projects",
        ["tenant_id", "updated_at", "created_at"],
        unique=False,
    )
    op.create_index(op.f("ix_projects_tenant_id"), "projects", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_tenant_id"), table_name="projects")
    op.drop_index("ix_projects_tenant_id_updated_at_created_at", table_name="projects")
    op.drop_table("projects")
