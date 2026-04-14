from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.artifacts.application import (
    ExportReportUseCase,
    PersistExportArtifactsUseCase,
)
from researchlens.modules.artifacts.infrastructure import (
    FilesystemArtifactStore,
    SqlAlchemyArtifactRepository,
    SqlAlchemyExportBundleReader,
)
from researchlens.modules.artifacts.infrastructure.rows import (
    ArtifactDownloadRecordRow,
    ArtifactRow,
)
from researchlens.modules.drafting.infrastructure import (
    SqlAlchemyDraftingRepository,
    SqlAlchemyDraftingRunInputReader,
)
from researchlens.modules.drafting.orchestration import (
    DraftingGraphRuntime,
    build_drafting_subgraph,
)
from researchlens.modules.evidence.infrastructure import SqlAlchemyEvidenceQueries
from researchlens.shared.config import get_settings, reset_settings_cache
from researchlens.shared.db import DatabaseRuntime

from .drafting_support import FakeDraftingClient, seed_run_with_retrieval_outputs


class _NoopEventWriter:
    async def info(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        return None

    async def warning(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        return None


class _NoopCheckpointWriter:
    async def checkpoint(
        self,
        *,
        key: str,
        summary: dict[str, object],
        completed_stages: tuple[str, ...],
        next_stage: str | None,
    ) -> None:
        return None


class _NoCancelProbe:
    async def cancel_requested(self, *, run_id: UUID) -> bool:
        return False


@pytest.mark.asyncio
async def test_phase10_exports_artifacts_and_reads_evidence_summary(
    database_runtime: DatabaseRuntime,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("STORAGE_LOCAL_ARTIFACT_ROOT", str(tmp_path))
    reset_settings_cache()
    async with database_runtime.session_factory() as session:
        tenant_id, run_id = await seed_run_with_retrieval_outputs(
            session,
            section_ids=("overview",),
        )
        await _draft(session, run_id)
        await _export(session, run_id)
        summary = await SqlAlchemyEvidenceQueries(session).run_summary(
            tenant_id=tenant_id,
            run_id=run_id,
        )
        trace = await SqlAlchemyEvidenceQueries(session).section_trace(
            tenant_id=tenant_id,
            run_id=run_id,
            section_id="overview",
        )
        artifact_count = await session.scalar(
            select(func.count()).select_from(ArtifactRow).where(ArtifactRow.run_id == run_id)
        )
        await session.commit()

    assert summary is not None
    assert summary.section_count == 1
    assert summary.chunk_count == 1
    assert trace is not None
    assert len(trace.source_refs) == 1
    assert artifact_count == 2


@pytest.mark.asyncio
async def test_phase10_records_artifact_download(
    database_runtime: DatabaseRuntime,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("STORAGE_LOCAL_ARTIFACT_ROOT", str(tmp_path))
    reset_settings_cache()
    async with database_runtime.session_factory() as session:
        tenant_id, run_id = await seed_run_with_retrieval_outputs(
            session,
            section_ids=("overview",),
        )
        await _draft(session, run_id)
        await _export(session, run_id)
        repository = SqlAlchemyArtifactRepository(session)
        artifact = (await repository.list_for_run(tenant_id=tenant_id, run_id=run_id))[0]
        await repository.record_download(
            tenant_id=tenant_id,
            artifact_id=artifact.id,
            run_id=run_id,
            actor_user_id=tenant_id,
            request_id="req-1",
            user_agent="pytest",
        )
        download_count = await session.scalar(
            select(func.count()).select_from(ArtifactDownloadRecordRow)
        )
        await session.commit()

    assert download_count == 1


async def _draft(session: AsyncSession, run_id: UUID) -> None:
    runtime = DraftingGraphRuntime(
        settings=get_settings(),
        input_reader=SqlAlchemyDraftingRunInputReader(session),
        repository=SqlAlchemyDraftingRepository(session),
        cancellation_probe=_NoCancelProbe(),
        events=_NoopEventWriter(),
        checkpoints=_NoopCheckpointWriter(),
        generation_client=FakeDraftingClient(),
    )
    await build_drafting_subgraph(runtime).ainvoke(
        {"run_id": run_id, "completed_stages": ("retrieve",)}
    )


async def _export(session: AsyncSession, run_id: UUID) -> None:
    repository = SqlAlchemyArtifactRepository(session)
    store = FilesystemArtifactStore(root=get_settings().storage.local_artifact_root)
    use_case = ExportReportUseCase(
        bundle_reader=SqlAlchemyExportBundleReader(session),
        persist_artifacts=PersistExportArtifactsUseCase(repository=repository, storage=store),
    )
    await use_case.execute(run_id=run_id)
