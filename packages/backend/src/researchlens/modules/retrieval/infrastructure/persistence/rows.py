from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from researchlens.shared.db import Base


class RetrievalSourceRow(Base):
    __tablename__ = "retrieval_sources"
    __table_args__ = (
        UniqueConstraint("canonical_key", name="uq_retrieval_sources_canonical_key"),
        Index("ix_retrieval_sources_provider_record", "provider_name", "provider_record_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    canonical_key: Mapped[str] = mapped_column(String(300), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(80), nullable=False)
    provider_record_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    identifiers_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RetrievalSourceSnapshotRow(Base):
    __tablename__ = "retrieval_source_snapshots"
    __table_args__ = (
        UniqueConstraint("source_id", "content_hash", name="uq_retrieval_snapshots_source_hash"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    source_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("retrieval_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RetrievalSourceChunkRow(Base):
    __tablename__ = "retrieval_source_chunks"
    __table_args__ = (UniqueConstraint("snapshot_id", "chunk_index"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    snapshot_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("retrieval_source_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RetrievalChunkEmbeddingRow(Base):
    __tablename__ = "retrieval_chunk_embeddings"
    __table_args__ = (UniqueConstraint("text_hash", "model"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    chunk_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("retrieval_source_chunks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    embedding_json: Mapped[list[float]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RunRetrievalSourceRow(Base):
    __tablename__ = "run_retrieval_sources"
    __table_args__ = (UniqueConstraint("run_id", "source_id"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("retrieval_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_section: Mapped[str | None] = mapped_column(String(120), nullable=True)
    query_intent: Mapped[str | None] = mapped_column(String(120), nullable=True)
    rank: Mapped[int] = mapped_column(nullable=False)
    score: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
