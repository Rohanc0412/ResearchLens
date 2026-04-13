from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from researchlens.modules.artifacts.application import (
    DownloadArtifactUseCase,
    GetArtifactDetailUseCase,
    ListRunArtifactsUseCase,
    PersistExportArtifactsUseCase,
)
from researchlens.modules.artifacts.infrastructure.artifact_repository_sql import (
    SqlAlchemyArtifactRepository,
)
from researchlens.modules.artifacts.infrastructure.filesystem_artifact_store import (
    FilesystemArtifactStore,
)
from researchlens.shared.config import ResearchLensSettings


@dataclass(slots=True)
class ArtifactsRequestContext:
    list_run_artifacts: ListRunArtifactsUseCase
    get_artifact_detail: GetArtifactDetailUseCase
    download_artifact: DownloadArtifactUseCase


class SqlAlchemyArtifactsRuntime:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        settings: ResearchLensSettings,
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings

    @asynccontextmanager
    async def request_context(self) -> AsyncIterator[ArtifactsRequestContext]:
        async with self._session_factory() as session:
            repository = SqlAlchemyArtifactRepository(session)
            storage = FilesystemArtifactStore(root=self._settings.storage.local_artifact_root)
            try:
                yield ArtifactsRequestContext(
                    list_run_artifacts=ListRunArtifactsUseCase(repository),
                    get_artifact_detail=GetArtifactDetailUseCase(repository),
                    download_artifact=DownloadArtifactUseCase(
                        repository=repository,
                        storage=storage,
                    ),
                )
                await session.commit()
            except Exception:
                await session.rollback()
                raise


def build_persist_export_artifacts(
    *,
    session: AsyncSession,
    settings: ResearchLensSettings,
) -> PersistExportArtifactsUseCase:
    return PersistExportArtifactsUseCase(
        repository=SqlAlchemyArtifactRepository(session),
        storage=FilesystemArtifactStore(root=settings.storage.local_artifact_root),
    )
