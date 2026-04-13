from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.artifacts.application.ports import (
    ArtifactDownload,
    ArtifactRepository,
    ArtifactStorage,
)
from researchlens.modules.artifacts.domain.export_models import PersistedArtifact
from researchlens.shared.errors import NotFoundError


@dataclass(frozen=True, slots=True)
class ArtifactQuery:
    tenant_id: UUID
    run_id: UUID | None = None
    artifact_id: UUID | None = None


class ListRunArtifactsUseCase:
    def __init__(self, repository: ArtifactRepository) -> None:
        self._repository = repository

    async def execute(self, query: ArtifactQuery) -> tuple[PersistedArtifact, ...]:
        if query.run_id is None:
            return ()
        return await self._repository.list_for_run(tenant_id=query.tenant_id, run_id=query.run_id)


class GetArtifactDetailUseCase:
    def __init__(self, repository: ArtifactRepository) -> None:
        self._repository = repository

    async def execute(self, query: ArtifactQuery) -> PersistedArtifact | None:
        if query.artifact_id is None:
            return None
        return await self._repository.get_for_tenant(
            tenant_id=query.tenant_id,
            artifact_id=query.artifact_id,
        )


class DownloadArtifactUseCase:
    def __init__(self, *, repository: ArtifactRepository, storage: ArtifactStorage) -> None:
        self._repository = repository
        self._storage = storage

    async def execute(
        self,
        *,
        tenant_id: UUID,
        actor_user_id: UUID,
        artifact_id: UUID,
        request_id: str | None,
        user_agent: str | None,
    ) -> ArtifactDownload:
        artifact = await self._repository.get_for_tenant(
            tenant_id=tenant_id,
            artifact_id=artifact_id,
        )
        if artifact is None:
            raise NotFoundError("Artifact was not found.")
        content = await self._storage.read(storage_key=artifact.storage_key)
        await self._repository.record_download(
            tenant_id=tenant_id,
            artifact_id=artifact.id,
            run_id=artifact.run_id,
            actor_user_id=actor_user_id,
            request_id=request_id,
            user_agent=user_agent,
        )
        return ArtifactDownload(
            filename=artifact.filename,
            media_type=artifact.media_type,
            content=content,
        )
