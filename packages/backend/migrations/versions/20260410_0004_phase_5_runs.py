"""phase 5 runs lifecycle

Revision ID: 20260410_0004
Revises: 20260410_0003
Create Date: 2026-04-10 18:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260410_0004"
down_revision: str | None = "20260410_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_stage", sa.String(length=32), nullable=True),
        sa.Column("output_type", sa.String(length=64), nullable=False),
        sa.Column("trigger_message_id", sa.Uuid(), nullable=True),
        sa.Column("client_request_id", sa.String(length=200), nullable=True),
        sa.Column("cancel_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_reason", sa.String(length=4000), nullable=True),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("last_event_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_runs_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("fk_runs_conversation_id_conversations"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["trigger_message_id"],
            ["messages.id"],
            name=op.f("fk_runs_trigger_message_id_messages"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_runs")),
        sa.UniqueConstraint(
            "tenant_id",
            "conversation_id",
            "client_request_id",
            name=op.f("uq_runs_tenant_id"),
        ),
    )
    op.create_index(op.f("ix_runs_tenant_id"), "runs", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_runs_project_id"), "runs", ["project_id"], unique=False)
    op.create_index(op.f("ix_runs_conversation_id"), "runs", ["conversation_id"], unique=False)
    op.create_index(
        op.f("ix_runs_created_by_user_id"),
        "runs",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_runs_tenant_project_created",
        "runs",
        ["tenant_id", "project_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_runs_tenant_status_updated",
        "runs",
        ["tenant_id", "status", "updated_at"],
        unique=False,
    )

    op.create_table(
        "run_status_transitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=False),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=120), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name=op.f("fk_run_status_transitions_run_id_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_run_status_transitions")),
    )
    op.create_index(
        op.f("ix_run_status_transitions_run_id"),
        "run_status_transitions",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        "ix_run_status_transitions_run_changed",
        "run_status_transitions",
        ["run_id", "changed_at"],
        unique=False,
    )

    op.create_table(
        "run_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("event_number", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("audience", sa.String(length=32), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_key", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name=op.f("fk_run_events_run_id_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_run_events")),
        sa.UniqueConstraint("run_id", "event_number", name=op.f("uq_run_events_run_id")),
        sa.UniqueConstraint("run_id", "event_key", name="uq_run_events_run_event_key"),
    )
    op.create_index(op.f("ix_run_events_run_id"), "run_events", ["run_id"], unique=False)
    op.create_index(
        "ix_run_events_run_event_number",
        "run_events",
        ["run_id", "event_number"],
        unique=False,
    )

    op.create_table(
        "run_checkpoints",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("checkpoint_key", sa.String(length=200), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("summary_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name=op.f("fk_run_checkpoints_run_id_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_run_checkpoints")),
        sa.UniqueConstraint(
            "run_id",
            "checkpoint_key",
            name=op.f("uq_run_checkpoints_run_id"),
        ),
    )
    op.create_index(
        op.f("ix_run_checkpoints_run_id"),
        "run_checkpoints",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        "ix_run_checkpoints_run_created",
        "run_checkpoints",
        ["run_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "run_queue_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_token", sa.Uuid(), nullable=True),
        sa.Column("leased_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.String(length=4000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name=op.f("fk_run_queue_items_run_id_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_run_queue_items")),
    )
    op.create_index(
        op.f("ix_run_queue_items_tenant_id"),
        "run_queue_items",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_run_queue_items_run_id"),
        "run_queue_items",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        "ix_run_queue_items_claim",
        "run_queue_items",
        ["status", "available_at", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_run_queue_items_active_run",
        "run_queue_items",
        ["run_id"],
        unique=True,
        sqlite_where=sa.text("status in ('queued', 'leased')"),
        postgresql_where=sa.text("status in ('queued', 'leased')"),
    )


def downgrade() -> None:
    op.drop_index("ix_run_queue_items_active_run", table_name="run_queue_items")
    op.drop_index("ix_run_queue_items_claim", table_name="run_queue_items")
    op.drop_index(op.f("ix_run_queue_items_run_id"), table_name="run_queue_items")
    op.drop_index(op.f("ix_run_queue_items_tenant_id"), table_name="run_queue_items")
    op.drop_table("run_queue_items")

    op.drop_index("ix_run_checkpoints_run_created", table_name="run_checkpoints")
    op.drop_index(op.f("ix_run_checkpoints_run_id"), table_name="run_checkpoints")
    op.drop_table("run_checkpoints")

    op.drop_index("ix_run_events_run_event_number", table_name="run_events")
    op.drop_index(op.f("ix_run_events_run_id"), table_name="run_events")
    op.drop_table("run_events")

    op.drop_index("ix_run_status_transitions_run_changed", table_name="run_status_transitions")
    op.drop_index(
        op.f("ix_run_status_transitions_run_id"),
        table_name="run_status_transitions",
    )
    op.drop_table("run_status_transitions")

    op.drop_index("ix_runs_tenant_status_updated", table_name="runs")
    op.drop_index("ix_runs_tenant_project_created", table_name="runs")
    op.drop_index(op.f("ix_runs_created_by_user_id"), table_name="runs")
    op.drop_index(op.f("ix_runs_conversation_id"), table_name="runs")
    op.drop_index(op.f("ix_runs_project_id"), table_name="runs")
    op.drop_index(op.f("ix_runs_tenant_id"), table_name="runs")
    op.drop_table("runs")
