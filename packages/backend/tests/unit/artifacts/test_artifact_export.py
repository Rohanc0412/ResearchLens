from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.artifacts.application.citation_resolution import resolve_citations
from researchlens.modules.artifacts.application.persist_export_artifacts import (
    PersistExportArtifactsUseCase,
)
from researchlens.modules.artifacts.domain import (
    ExportChunk,
    ExportSource,
    FinalSection,
    ReportExportBundle,
)
from researchlens.modules.artifacts.infrastructure import (
    FilesystemArtifactStore,
    SqlAlchemyArtifactRepository,
)
from researchlens.modules.projects.infrastructure.project_row import ProjectRow
from researchlens.modules.runs.infrastructure.rows import RunRow
from researchlens.shared.db import DatabaseRuntime
from researchlens.shared.errors import ValidationError


@pytest.mark.asyncio
async def test_filesystem_artifact_store_writes_reads_and_hashes(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(root=tmp_path)

    stored = await store.write(storage_key="tenant/run/report.md", content=b"report")

    assert await store.read(storage_key=stored.storage_key) == b"report"
    assert stored.backend == "local"
    assert stored.byte_size == 6
    assert len(stored.sha256) == 64


def test_citation_resolution_rejects_unknown_chunk() -> None:
    with pytest.raises(ValidationError, match="unknown chunk"):
        resolve_citations(
            section_texts=(f"Claim [[chunk:{uuid4()}]]",),
            chunks=(),
        )


def test_citation_resolution_maps_chunks_to_stable_labels() -> None:
    chunk_id = uuid4()
    source_id = uuid4()

    citations = resolve_citations(
        section_texts=(f"Claim [[chunk:{chunk_id}]] and again [[chunk:{chunk_id}]]",),
        chunks=(ExportChunk(chunk_id=chunk_id, source_id=source_id, chunk_index=0, text="x"),),
    )

    assert len(citations) == 1
    assert citations[0].citation_label == "C1"
    assert citations[0].source_id == source_id


@pytest.mark.asyncio
async def test_artifact_persistence_is_idempotent(
    database_runtime: DatabaseRuntime,
    tmp_path: Path,
) -> None:
    bundle = _bundle()
    async with database_runtime.session_factory() as session:
        _add_run_row(session, bundle=bundle)
        repository = SqlAlchemyArtifactRepository(session)
        store = FilesystemArtifactStore(root=tmp_path)
        use_case = PersistExportArtifactsUseCase(repository=repository, storage=store)

        first = await use_case.execute(bundle=bundle)
        second = await use_case.execute(bundle=bundle)
        await session.commit()

    assert tuple(item.id for item in first) == tuple(item.id for item in second)


def _add_run_row(session: AsyncSession, *, bundle: ReportExportBundle) -> None:
    now = datetime.now(tz=UTC)
    user_id = uuid4()
    session.add(
        ProjectRow(
            id=bundle.project_id,
            tenant_id=bundle.tenant_id,
            name="Project",
            description=None,
            created_by=str(user_id),
            created_at=now,
            updated_at=now,
        )
    )
    session.add(
        RunRow(
            id=bundle.run_id,
            tenant_id=bundle.tenant_id,
            project_id=bundle.project_id,
            conversation_id=None,
            created_by_user_id=user_id,
            status="running",
            current_stage="export",
            output_type="report",
            trigger_message_id=None,
            client_request_id=None,
            cancel_requested_at=None,
            started_at=now,
            finished_at=None,
            retry_count=0,
            failure_reason=None,
            error_code=None,
            last_event_number=0,
            created_at=now,
            updated_at=now,
        )
    )


def _bundle() -> ReportExportBundle:
    tenant_id = uuid4()
    project_id = uuid4()
    run_id = uuid4()
    chunk_id = uuid4()
    source_id = uuid4()
    now = datetime.now(tz=UTC)
    return ReportExportBundle(
        tenant_id=tenant_id,
        project_id=project_id,
        run_id=run_id,
        conversation_id=None,
        report_title="Report",
        sections=(
            FinalSection(
                section_id="overview",
                title="Overview",
                section_order=1,
                text=f"Grounded [[chunk:{chunk_id}]]",
                summary="Grounded",
                repaired=False,
                draft_id=uuid4(),
                repair_result_id=None,
            ),
        ),
        chunks=(ExportChunk(chunk_id=chunk_id, source_id=source_id, chunk_index=0, text="chunk"),),
        sources=(
            ExportSource(
                source_id=source_id,
                canonical_key="source",
                title="Source",
                identifiers={},
                metadata={"created_at": now.isoformat()},
            ),
        ),
        citations=resolve_citations(
            section_texts=(f"Grounded [[chunk:{chunk_id}]]",),
            chunks=(
                ExportChunk(chunk_id=chunk_id, source_id=source_id, chunk_index=0, text="chunk"),
            ),
        ),
        latest_evaluation_pass_id=None,
        latest_repair_pass_id=None,
        warnings=(),
    )
