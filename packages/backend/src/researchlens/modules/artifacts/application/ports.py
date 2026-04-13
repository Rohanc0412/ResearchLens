from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from researchlens.modules.artifacts.domain.export_models import (
    PersistedArtifact,
    PersistedManifest,
    RenderedArtifact,
    ReportExportBundle,
)


@dataclass(frozen=True, slots=True)
class StoredArtifactBytes:
    backend: str
    storage_key: str
    byte_size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class ArtifactDownload:
    filename: str
    media_type: str
    content: bytes


class ArtifactStorage(Protocol):
    async def write(self, *, storage_key: str, content: bytes) -> StoredArtifactBytes: ...

    async def read(self, *, storage_key: str) -> bytes: ...


class ExportBundleReader(Protocol):
    async def load_bundle(self, *, run_id: UUID) -> ReportExportBundle: ...


class ArtifactRepository(Protocol):
    async def upsert_artifact(
        self,
        *,
        bundle: ReportExportBundle,
        artifact: RenderedArtifact,
        stored: StoredArtifactBytes,
    ) -> PersistedArtifact: ...

    async def upsert_manifest(
        self,
        *,
        bundle: ReportExportBundle,
        artifact_ids: tuple[UUID, ...],
        manifest_json: dict[str, object],
    ) -> PersistedManifest: ...

    async def attach_manifest(
        self,
        *,
        run_id: UUID,
        manifest_artifact_id: UUID,
        manifest_id: UUID,
    ) -> None: ...

    async def list_for_run(self, *, tenant_id: UUID, run_id: UUID) -> tuple[PersistedArtifact, ...]:
        ...

    async def get_for_tenant(
        self,
        *,
        tenant_id: UUID,
        artifact_id: UUID,
    ) -> PersistedArtifact | None: ...

    async def record_download(
        self,
        *,
        tenant_id: UUID,
        artifact_id: UUID,
        run_id: UUID,
        actor_user_id: UUID,
        request_id: str | None,
        user_agent: str | None,
    ) -> None: ...

    async def download_count(self, *, artifact_id: UUID) -> int: ...
