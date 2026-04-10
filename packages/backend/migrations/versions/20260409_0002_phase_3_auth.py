"""phase 3 auth module

Revision ID: 20260409_0002
Revises: 20260408_0001
Create Date: 2026-04-09 21:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260409_0002"
down_revision: str | None = "20260408_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("roles", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_users")),
        sa.UniqueConstraint("email", name=op.f("uq_auth_users_email")),
        sa.UniqueConstraint("username", name=op.f("uq_auth_users_username")),
    )
    op.create_index("ix_auth_users_tenant_id", "auth_users", ["tenant_id"], unique=False)
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["auth_users.id"],
            name=op.f("fk_auth_sessions_user_id_auth_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_sessions")),
    )
    op.create_index("ix_auth_sessions_tenant_id", "auth_sessions", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_auth_sessions_user_id"), "auth_sessions", ["user_id"], unique=False)
    op.create_table(
        "auth_password_resets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["auth_users.id"],
            name=op.f("fk_auth_password_resets_user_id_auth_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_password_resets")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_auth_password_resets_token_hash")),
    )
    op.create_index(
        "ix_auth_password_resets_tenant_id",
        "auth_password_resets",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_password_resets_user_id"),
        "auth_password_resets",
        ["user_id"],
        unique=False,
    )
    op.create_table(
        "auth_refresh_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rotated_from_id", sa.Uuid(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["auth_sessions.id"],
            name=op.f("fk_auth_refresh_tokens_session_id_auth_sessions"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["auth_users.id"],
            name=op.f("fk_auth_refresh_tokens_user_id_auth_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_refresh_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_auth_refresh_tokens_token_hash")),
    )
    op.create_index(
        "ix_auth_refresh_tokens_tenant_id",
        "auth_refresh_tokens",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_refresh_tokens_session_id"),
        "auth_refresh_tokens",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_refresh_tokens_user_id"),
        "auth_refresh_tokens",
        ["user_id"],
        unique=False,
    )
    op.create_table(
        "auth_mfa_factors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("factor_type", sa.String(length=32), nullable=False),
        sa.Column("secret", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("enabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["auth_users.id"],
            name=op.f("fk_auth_mfa_factors_user_id_auth_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_mfa_factors")),
        sa.UniqueConstraint("user_id", "factor_type", name=op.f("uq_auth_mfa_factors_user_id")),
    )
    op.create_index(
        "ix_auth_mfa_factors_tenant_id",
        "auth_mfa_factors",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_mfa_factors_user_id"),
        "auth_mfa_factors",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_auth_mfa_factors_user_id"), table_name="auth_mfa_factors")
    op.drop_index("ix_auth_mfa_factors_tenant_id", table_name="auth_mfa_factors")
    op.drop_table("auth_mfa_factors")
    op.drop_index(op.f("ix_auth_refresh_tokens_user_id"), table_name="auth_refresh_tokens")
    op.drop_index(op.f("ix_auth_refresh_tokens_session_id"), table_name="auth_refresh_tokens")
    op.drop_index("ix_auth_refresh_tokens_tenant_id", table_name="auth_refresh_tokens")
    op.drop_table("auth_refresh_tokens")
    op.drop_index(op.f("ix_auth_password_resets_user_id"), table_name="auth_password_resets")
    op.drop_index("ix_auth_password_resets_tenant_id", table_name="auth_password_resets")
    op.drop_table("auth_password_resets")
    op.drop_index(op.f("ix_auth_sessions_user_id"), table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_tenant_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_index("ix_auth_users_tenant_id", table_name="auth_users")
    op.drop_table("auth_users")
