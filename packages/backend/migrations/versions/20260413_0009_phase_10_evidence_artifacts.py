"""phase 10 evidence artifacts

Revision ID: 20260413_0009
Revises: 20260413_0008
Create Date: 2026-04-13 00:09:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260413_0009"
down_revision: str | None = "20260413_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "artifacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("artifact_kind", sa.String(length=80), nullable=False),
        sa.Column("filename", sa.String(length=260), nullable=False),
        sa.Column("media_type", sa.String(length=160), nullable=False),
        sa.Column("storage_backend", sa.String(length=40), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("manifest_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "artifact_kind", name="uq_artifacts_run_kind"),
    )
    op.create_index("ix_artifacts_tenant_id", "artifacts", ["tenant_id"])
    op.create_index("ix_artifacts_project_id", "artifacts", ["project_id"])
    op.create_index("ix_artifacts_run_id", "artifacts", ["run_id"])
    op.create_index("ix_artifacts_tenant_run", "artifacts", ["tenant_id", "run_id", "created_at"])

    op.create_table(
        "artifact_manifests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("report_title", sa.String(length=240), nullable=False),
        sa.Column("artifact_ids_json", sa.JSON(), nullable=False),
        sa.Column("final_sections_json", sa.JSON(), nullable=False),
        sa.Column("source_refs_json", sa.JSON(), nullable=False),
        sa.Column("citation_map_json", sa.JSON(), nullable=False),
        sa.Column("latest_evaluation_pass_id", sa.Uuid(), nullable=True),
        sa.Column("latest_repair_pass_id", sa.Uuid(), nullable=True),
        sa.Column("export_warnings_json", sa.JSON(), nullable=False),
        sa.Column("manifest_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", name="uq_artifact_manifests_run"),
    )
    op.create_index("ix_artifact_manifests_tenant_id", "artifact_manifests", ["tenant_id"])
    op.create_index("ix_artifact_manifests_project_id", "artifact_manifests", ["project_id"])
    op.create_index("ix_artifact_manifests_run_id", "artifact_manifests", ["run_id"])
    op.create_index(
        "ix_artifact_manifests_tenant_run",
        "artifact_manifests",
        ["tenant_id", "run_id"],
    )

    op.create_table(
        "artifact_download_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("artifact_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.String(length=120), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_artifact_download_records_tenant_id",
        "artifact_download_records",
        ["tenant_id"],
    )
    op.create_index("ix_artifact_download_records_run_id", "artifact_download_records", ["run_id"])
    op.create_index(
        "ix_artifact_download_records_actor_user_id",
        "artifact_download_records",
        ["actor_user_id"],
    )
    op.create_index(
        "ix_artifact_downloads_artifact",
        "artifact_download_records",
        ["artifact_id", "downloaded_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_artifact_downloads_artifact", table_name="artifact_download_records")
    op.drop_index(
        "ix_artifact_download_records_actor_user_id",
        table_name="artifact_download_records",
    )
    op.drop_index("ix_artifact_download_records_run_id", table_name="artifact_download_records")
    op.drop_index("ix_artifact_download_records_tenant_id", table_name="artifact_download_records")
    op.drop_table("artifact_download_records")
    op.drop_index("ix_artifact_manifests_tenant_run", table_name="artifact_manifests")
    op.drop_index("ix_artifact_manifests_run_id", table_name="artifact_manifests")
    op.drop_index("ix_artifact_manifests_project_id", table_name="artifact_manifests")
    op.drop_index("ix_artifact_manifests_tenant_id", table_name="artifact_manifests")
    op.drop_table("artifact_manifests")
    op.drop_index("ix_artifacts_tenant_run", table_name="artifacts")
    op.drop_index("ix_artifacts_run_id", table_name="artifacts")
    op.drop_index("ix_artifacts_project_id", table_name="artifacts")
    op.drop_index("ix_artifacts_tenant_id", table_name="artifacts")
    op.drop_table("artifacts")
