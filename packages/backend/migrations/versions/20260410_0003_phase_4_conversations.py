"""phase 4 conversations core

Revision ID: 20260410_0003
Revises: 20260409_0002
Create Date: 2026-04-10 10:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260410_0003"
down_revision: str | None = "20260409_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_conversations_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversations")),
    )
    op.create_index(
        op.f("ix_conversations_tenant_id"), "conversations", ["tenant_id"], unique=False
    )
    op.create_index(
        op.f("ix_conversations_project_id"),
        "conversations",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversations_created_by_user_id"),
        "conversations",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversations_tenant_project_last_message_created_id",
        "conversations",
        ["tenant_id", "project_id", "last_message_at", "created_at", "id"],
        unique=False,
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("content_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("client_message_id", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("fk_messages_conversation_id_conversations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
        sa.UniqueConstraint(
            "tenant_id",
            "conversation_id",
            "client_message_id",
            name=op.f("uq_messages_tenant_id"),
        ),
    )
    op.create_index(op.f("ix_messages_tenant_id"), "messages", ["tenant_id"], unique=False)
    op.create_index(
        op.f("ix_messages_conversation_id"),
        "messages",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        "ix_messages_tenant_conversation_created_id",
        "messages",
        ["tenant_id", "conversation_id", "created_at", "id"],
        unique=False,
    )

    op.create_table(
        "conversation_run_triggers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("source_message_id", sa.Uuid(), nullable=True),
        sa.Column("request_text", sa.Text(), nullable=False),
        sa.Column("client_request_id", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f("fk_conversation_run_triggers_conversation_id_conversations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_message_id"],
            ["messages.id"],
            name=op.f("fk_conversation_run_triggers_source_message_id_messages"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation_run_triggers")),
    )
    op.create_index(
        op.f("ix_conversation_run_triggers_tenant_id"),
        "conversation_run_triggers",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversation_run_triggers_conversation_id"),
        "conversation_run_triggers",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversation_run_triggers_project_id"),
        "conversation_run_triggers",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversation_run_triggers_created_by_user_id"),
        "conversation_run_triggers",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_run_triggers_tenant_conversation_created",
        "conversation_run_triggers",
        ["tenant_id", "conversation_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_conversation_run_triggers_tenant_conversation_created",
        table_name="conversation_run_triggers",
    )
    op.drop_index(
        op.f("ix_conversation_run_triggers_created_by_user_id"),
        table_name="conversation_run_triggers",
    )
    op.drop_index(
        op.f("ix_conversation_run_triggers_project_id"),
        table_name="conversation_run_triggers",
    )
    op.drop_index(
        op.f("ix_conversation_run_triggers_conversation_id"),
        table_name="conversation_run_triggers",
    )
    op.drop_index(
        op.f("ix_conversation_run_triggers_tenant_id"),
        table_name="conversation_run_triggers",
    )
    op.drop_table("conversation_run_triggers")

    op.drop_index("ix_messages_tenant_conversation_created_id", table_name="messages")
    op.drop_index(op.f("ix_messages_conversation_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_tenant_id"), table_name="messages")
    op.drop_table("messages")

    op.drop_index(
        "ix_conversations_tenant_project_last_message_created_id",
        table_name="conversations",
    )
    op.drop_index(
        op.f("ix_conversations_created_by_user_id"),
        table_name="conversations",
    )
    op.drop_index(op.f("ix_conversations_project_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_tenant_id"), table_name="conversations")
    op.drop_table("conversations")
