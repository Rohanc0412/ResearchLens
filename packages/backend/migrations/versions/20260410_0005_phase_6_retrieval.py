"""phase 6 retrieval persistence

Revision ID: 20260410_0005
Revises: 20260410_0004
Create Date: 2026-04-10 23:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260410_0005"
down_revision: str | None = "20260410_0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "retrieval_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("canonical_key", sa.String(length=300), nullable=False),
        sa.Column("provider_name", sa.String(length=80), nullable=False),
        sa.Column("provider_record_id", sa.String(length=200), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("identifiers_json", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_retrieval_sources")),
        sa.UniqueConstraint("canonical_key", name="uq_retrieval_sources_canonical_key"),
    )
    op.create_index(
        "ix_retrieval_sources_provider_record",
        "retrieval_sources",
        ["provider_name", "provider_record_id"],
        unique=False,
    )

    op.create_table(
        "retrieval_source_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("content_kind", sa.String(length=32), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["retrieval_sources.id"],
            name=op.f("fk_retrieval_source_snapshots_source_id_retrieval_sources"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_retrieval_source_snapshots")),
        sa.UniqueConstraint("source_id", "content_hash", name="uq_retrieval_snapshots_source_hash"),
    )
    op.create_index(
        op.f("ix_retrieval_source_snapshots_source_id"),
        "retrieval_source_snapshots",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_retrieval_source_snapshots_content_hash"),
        "retrieval_source_snapshots",
        ["content_hash"],
        unique=False,
    )

    op.create_table(
        "retrieval_source_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text_hash", sa.String(length=64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["retrieval_source_snapshots.id"],
            name=op.f("fk_retrieval_source_chunks_snapshot_id_retrieval_source_snapshots"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_retrieval_source_chunks")),
        sa.UniqueConstraint("snapshot_id", "chunk_index", name=op.f("uq_retrieval_source_chunks_snapshot_id")),
    )
    op.create_index(
        op.f("ix_retrieval_source_chunks_snapshot_id"),
        "retrieval_source_chunks",
        ["snapshot_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_retrieval_source_chunks_text_hash"),
        "retrieval_source_chunks",
        ["text_hash"],
        unique=False,
    )

    op.create_table(
        "retrieval_chunk_embeddings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("chunk_id", sa.Uuid(), nullable=True),
        sa.Column("text_hash", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("embedding_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["chunk_id"],
            ["retrieval_source_chunks.id"],
            name=op.f("fk_retrieval_chunk_embeddings_chunk_id_retrieval_source_chunks"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_retrieval_chunk_embeddings")),
        sa.UniqueConstraint("text_hash", "model", name=op.f("uq_retrieval_chunk_embeddings_text_hash")),
    )
    op.create_index(
        op.f("ix_retrieval_chunk_embeddings_chunk_id"),
        "retrieval_chunk_embeddings",
        ["chunk_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_retrieval_chunk_embeddings_text_hash"),
        "retrieval_chunk_embeddings",
        ["text_hash"],
        unique=False,
    )

    op.create_table(
        "run_retrieval_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("target_section", sa.String(length=120), nullable=True),
        sa.Column("query_intent", sa.String(length=120), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name=op.f("fk_run_retrieval_sources_run_id_runs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["retrieval_sources.id"],
            name=op.f("fk_run_retrieval_sources_source_id_retrieval_sources"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_run_retrieval_sources")),
        sa.UniqueConstraint("run_id", "source_id", name=op.f("uq_run_retrieval_sources_run_id")),
    )
    op.create_index(
        op.f("ix_run_retrieval_sources_run_id"),
        "run_retrieval_sources",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_run_retrieval_sources_source_id"),
        "run_retrieval_sources",
        ["source_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_run_retrieval_sources_source_id"), table_name="run_retrieval_sources")
    op.drop_index(op.f("ix_run_retrieval_sources_run_id"), table_name="run_retrieval_sources")
    op.drop_table("run_retrieval_sources")
    op.drop_index(op.f("ix_retrieval_chunk_embeddings_text_hash"), table_name="retrieval_chunk_embeddings")
    op.drop_index(op.f("ix_retrieval_chunk_embeddings_chunk_id"), table_name="retrieval_chunk_embeddings")
    op.drop_table("retrieval_chunk_embeddings")
    op.drop_index(op.f("ix_retrieval_source_chunks_text_hash"), table_name="retrieval_source_chunks")
    op.drop_index(op.f("ix_retrieval_source_chunks_snapshot_id"), table_name="retrieval_source_chunks")
    op.drop_table("retrieval_source_chunks")
    op.drop_index(op.f("ix_retrieval_source_snapshots_content_hash"), table_name="retrieval_source_snapshots")
    op.drop_index(op.f("ix_retrieval_source_snapshots_source_id"), table_name="retrieval_source_snapshots")
    op.drop_table("retrieval_source_snapshots")
    op.drop_index("ix_retrieval_sources_provider_record", table_name="retrieval_sources")
    op.drop_table("retrieval_sources")
