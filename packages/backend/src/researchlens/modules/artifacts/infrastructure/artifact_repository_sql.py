from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.artifacts.application.ports import ArtifactRepository, StoredArtifactBytes
from researchlens.modules.artifacts.domain.export_models import (
    PersistedArtifact,
    PersistedManifest,
    RenderedArtifact,
    ReportExportBundle,
)
from researchlens.modules.artifacts.infrastructure.rows import (
    ArtifactDownloadRecordRow,
    ArtifactManifestRow,
    ArtifactRow,
)


class SqlAlchemyArtifactRepository(ArtifactRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_artifact(
        self,
        *,
        bundle: ReportExportBundle,
        artifact: RenderedArtifact,
        stored: StoredArtifactBytes,
    ) -> PersistedArtifact:
        row = await self._session.scalar(
            select(ArtifactRow).where(
                ArtifactRow.run_id == bundle.run_id,
                ArtifactRow.artifact_kind == artifact.kind,
            )
        )
        now = datetime.now(tz=UTC)
        if row is None:
            row = ArtifactRow(
                id=uuid4(),
                tenant_id=bundle.tenant_id,
                project_id=bundle.project_id,
                run_id=bundle.run_id,
                artifact_kind=artifact.kind,
                created_at=now,
                updated_at=now,
                manifest_id=None,
                filename=artifact.filename,
                media_type=artifact.media_type,
                storage_backend=stored.backend,
                storage_key=stored.storage_key,
                byte_size=stored.byte_size,
                sha256=stored.sha256,
                metadata_json=artifact.metadata,
            )
            self._session.add(row)
        else:
            row.filename = artifact.filename
            row.media_type = artifact.media_type
            row.storage_backend = stored.backend
            row.storage_key = stored.storage_key
            row.byte_size = stored.byte_size
            row.sha256 = stored.sha256
            row.metadata_json = artifact.metadata
            row.updated_at = now
        await self._session.flush()
        return _artifact(row)

    async def upsert_manifest(
        self,
        *,
        bundle: ReportExportBundle,
        artifact_ids: tuple[UUID, ...],
        manifest_json: dict[str, object],
    ) -> PersistedManifest:
        row = await self._session.scalar(
            select(ArtifactManifestRow).where(ArtifactManifestRow.run_id == bundle.run_id)
        )
        now = datetime.now(tz=UTC)
        values = _manifest_values(bundle, artifact_ids, manifest_json)
        if row is None:
            row = ArtifactManifestRow(id=uuid4(), created_at=now, updated_at=now, **values)
            self._session.add(row)
        else:
            for key, value in values.items():
                setattr(row, key, value)
            row.updated_at = now
        await self._session.flush()
        return PersistedManifest(
            id=row.id,
            run_id=row.run_id,
            report_title=row.report_title,
            artifact_ids=tuple(UUID(item) for item in row.artifact_ids_json),
            created_at=row.created_at,
        )

    async def attach_manifest(
        self,
        *,
        run_id: UUID,
        manifest_artifact_id: UUID,
        manifest_id: UUID,
    ) -> None:
        row = await self._session.scalar(
            select(ArtifactRow).where(
                ArtifactRow.run_id == run_id,
                ArtifactRow.id == manifest_artifact_id,
            )
        )
        if row is not None:
            row.manifest_id = manifest_id
            row.updated_at = datetime.now(tz=UTC)
            await self._session.flush()

    async def list_for_run(self, *, tenant_id: UUID, run_id: UUID) -> tuple[PersistedArtifact, ...]:
        rows = (
            await self._session.scalars(
                select(ArtifactRow)
                .where(ArtifactRow.tenant_id == tenant_id, ArtifactRow.run_id == run_id)
                .order_by(ArtifactRow.created_at.asc(), ArtifactRow.artifact_kind.asc())
            )
        ).all()
        return tuple(_artifact(row) for row in rows)

    async def get_for_tenant(
        self,
        *,
        tenant_id: UUID,
        artifact_id: UUID,
    ) -> PersistedArtifact | None:
        row = await self._session.scalar(
            select(ArtifactRow).where(
                ArtifactRow.tenant_id == tenant_id,
                ArtifactRow.id == artifact_id,
            )
        )
        return _artifact(row) if row is not None else None

    async def record_download(
        self,
        *,
        tenant_id: UUID,
        artifact_id: UUID,
        run_id: UUID,
        actor_user_id: UUID,
        request_id: str | None,
        user_agent: str | None,
    ) -> None:
        self._session.add(
            ArtifactDownloadRecordRow(
                id=uuid4(),
                tenant_id=tenant_id,
                artifact_id=artifact_id,
                run_id=run_id,
                actor_user_id=actor_user_id,
                request_id=request_id,
                user_agent=user_agent,
                downloaded_at=datetime.now(tz=UTC),
            )
        )
        await self._session.flush()

    async def download_count(self, *, artifact_id: UUID) -> int:
        value = await self._session.scalar(
            select(func.count()).select_from(ArtifactDownloadRecordRow).where(
                ArtifactDownloadRecordRow.artifact_id == artifact_id
            )
        )
        return int(value or 0)


def _artifact(row: ArtifactRow) -> PersistedArtifact:
    return PersistedArtifact(
        id=row.id,
        run_id=row.run_id,
        kind=row.artifact_kind,
        filename=row.filename,
        media_type=row.media_type,
        storage_backend=row.storage_backend,
        storage_key=row.storage_key,
        byte_size=row.byte_size,
        sha256=row.sha256,
        created_at=row.created_at,
        manifest_id=row.manifest_id,
    )


def _manifest_values(
    bundle: ReportExportBundle,
    artifact_ids: tuple[UUID, ...],
    manifest_json: dict[str, object],
) -> dict[str, object]:
    return {
        "tenant_id": bundle.tenant_id,
        "project_id": bundle.project_id,
        "run_id": bundle.run_id,
        "report_title": bundle.report_title,
        "artifact_ids_json": [str(item) for item in artifact_ids],
        "final_sections_json": _object_list(manifest_json["sections"]),
        "source_refs_json": _object_list(manifest_json["sources"]),
        "citation_map_json": _object_list(manifest_json["citation_map"]),
        "latest_evaluation_pass_id": bundle.latest_evaluation_pass_id,
        "latest_repair_pass_id": bundle.latest_repair_pass_id,
        "export_warnings_json": list(bundle.warnings),
        "manifest_json": manifest_json,
    }


def _object_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, Iterable) or isinstance(value, str | bytes | dict):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]
