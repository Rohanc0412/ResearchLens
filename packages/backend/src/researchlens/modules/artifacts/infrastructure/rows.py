from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from researchlens.shared.db import Base


class ArtifactRow(Base):
    __tablename__ = "artifacts"
    __table_args__ = (
        UniqueConstraint("run_id", "artifact_kind", name="uq_artifacts_run_kind"),
        Index("ix_artifacts_tenant_run", "tenant_id", "run_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    project_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artifact_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    filename: Mapped[str] = mapped_column(String(260), nullable=False)
    media_type: Mapped[str] = mapped_column(String(160), nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(40), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    manifest_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ArtifactManifestRow(Base):
    __tablename__ = "artifact_manifests"
    __table_args__ = (
        UniqueConstraint("run_id", name="uq_artifact_manifests_run"),
        Index("ix_artifact_manifests_tenant_run", "tenant_id", "run_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    project_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_title: Mapped[str] = mapped_column(String(240), nullable=False)
    artifact_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    final_sections_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    source_refs_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    citation_map_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    latest_evaluation_pass_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    latest_repair_pass_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    export_warnings_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    manifest_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ArtifactDownloadRecordRow(Base):
    __tablename__ = "artifact_download_records"
    __table_args__ = (Index("ix_artifact_downloads_artifact", "artifact_id", "downloaded_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    artifact_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    actor_user_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    request_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    downloaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
