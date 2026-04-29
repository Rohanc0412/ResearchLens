import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from researchlens.modules.retrieval.domain.candidate import (
    CanonicalIdentifiers,
    NormalizedSearchCandidate,
    QueryProvenance,
    SourceProvenance,
)
from researchlens.modules.retrieval.domain.ranking_policy import RankedCandidate, ScoreBreakdown
from researchlens.modules.retrieval.domain.retrieval_outline import (
    RetrievalOutline,
    RetrievalOutlineSection,
)
from researchlens.modules.retrieval.infrastructure.ingestion.content_selection import (
    choose_ingestible_content,
)
from researchlens.modules.retrieval.infrastructure.persistence.rows import (
    RetrievalOutlineRow,
    RetrievalOutlineSectionRow,
    RetrievalChunkEmbeddingRow,
    RetrievalSourceChunkRow,
    RetrievalSourceRow,
    RetrievalSourceSnapshotRow,
)
from researchlens.modules.retrieval.infrastructure.persistence.source_repository_sql import (
    SqlAlchemyRetrievalIngestionRepository,
)
from researchlens.modules.projects.infrastructure.project_row import ProjectRow
from researchlens.modules.runs.infrastructure.rows import RunRow
from researchlens.shared.db import DatabaseRuntime
from researchlens.shared.embeddings.batching import (
    EmbeddingBatch,
    embed_batches_bounded,
    split_embedding_batches,
)
from researchlens.shared.embeddings.domain import EmbeddingRequest, EmbeddingResult


class _FakeEmbeddingClient:
    @property
    def model(self) -> str:
        return "text-embedding-3-small"

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        vectors = tuple((float(index + 1),) for index, _ in enumerate(request.texts))
        return EmbeddingResult(vectors=vectors)


def test_content_selection_prefers_full_text_then_abstract_then_title() -> None:
    assert choose_ingestible_content(title="T", abstract="A", full_text="F").text == "F"
    assert choose_ingestible_content(title="T", abstract="A", full_text=None).text == "A"
    assert choose_ingestible_content(title="T", abstract=None, full_text=None).text == "T"


def test_embedding_batches_respect_batch_size() -> None:
    batches = split_embedding_batches(["a", "b", "c"], batch_size=2)

    assert batches == [
        EmbeddingBatch(index=0, texts=("a", "b")),
        EmbeddingBatch(index=1, texts=("c",)),
    ]


@pytest.mark.asyncio
async def test_embed_batches_bounded_respects_concurrency() -> None:
    active = 0
    max_active = 0

    async def embed(texts: tuple[str, ...]) -> list[list[float]]:
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.01)
        active -= 1
        return [[float(len(text))] for text in texts]

    result = await embed_batches_bounded(
        batches=split_embedding_batches(["a", "bb", "ccc", "dddd"], batch_size=1),
        max_concurrent_batches=2,
        embed_batch=embed,
    )

    assert result == [[1.0], [2.0], [3.0], [4.0]]
    assert max_active == 2


@pytest.mark.asyncio
async def test_retrieval_ingestion_persists_chunk_before_embedding(
    database_runtime: DatabaseRuntime,
) -> None:
    candidate = NormalizedSearchCandidate(
        provider_name="openalex",
        provider_record_id="W123",
        identifiers=CanonicalIdentifiers(openalex_id="W123"),
        title="Melanoma biomarker review",
        authors=("Author",),
        year=2024,
        source_type="article",
        abstract="A concise abstract about melanoma biomarkers.",
        full_text=None,
        landing_page_url="https://example.com/paper",
        pdf_url=None,
        venue="Journal",
        citation_count=10,
        keywords=("melanoma",),
        retrieved_at=datetime.now(tz=UTC),
        provider_metadata={},
        provenance=(SourceProvenance(provider_name="openalex", provider_record_id="W123"),),
        query_provenance=QueryProvenance(
            source_query="melanoma biomarkers",
            intent="overview",
            target_section="overview",
        ),
    )
    ranked = RankedCandidate(
        candidate=candidate,
        score_breakdown=ScoreBreakdown(
            lexical=1.0,
            embedding=0.5,
            recency=1.0,
            citation=0.3,
            total=2.8,
        ),
    )

    async with database_runtime.session_factory() as session:
        repository = SqlAlchemyRetrievalIngestionRepository(
            session,
            embedding_model="text-embedding-3-small",
            embedding_client=_FakeEmbeddingClient(),
        )
        source_id = uuid4()
        snapshot_id = uuid4()
        session.add(
            RetrievalSourceRow(
                id=source_id,
                canonical_key=candidate.identifiers.canonical_key(candidate.title),
                provider_name=candidate.provider_name,
                provider_record_id=candidate.provider_record_id,
                title=candidate.title,
                identifiers_json={},
                metadata_json={},
                created_at=datetime.now(tz=UTC),
                updated_at=datetime.now(tz=UTC),
            )
        )
        session.add(
            RetrievalSourceSnapshotRow(
                id=snapshot_id,
                source_id=source_id,
                content_hash="snapshot-hash",
                content_kind="abstract",
                content_text=candidate.abstract or "",
                created_at=datetime.now(tz=UTC),
            )
        )
        await session.flush()

        await repository._insert_chunks(snapshot_id=snapshot_id, item=ranked)
        await session.commit()

        chunk_count = await session.scalar(
            select(func.count()).select_from(RetrievalSourceChunkRow)
        )
        embedding_count = await session.scalar(
            select(func.count()).select_from(RetrievalChunkEmbeddingRow)
        )
        embedding_chunk_ids = tuple(
            await session.scalars(select(RetrievalChunkEmbeddingRow.chunk_id))
        )

    assert chunk_count == 1
    assert embedding_count == 1
    assert embedding_chunk_ids[0] is not None


@pytest.mark.asyncio
async def test_retrieval_ingestion_persists_outline_metadata(
    database_runtime: DatabaseRuntime,
) -> None:
    tenant_id = uuid4()
    project_id = uuid4()
    run_id = uuid4()
    user_id = uuid4()
    outline = RetrievalOutline(
        report_title="AI Safety Benchmarking Outlook",
        sections=(
            RetrievalOutlineSection(
                section_id="s1",
                title="Recent Developments",
                goal="Summarize current progress.",
                suggested_evidence_themes=(),
                key_points=("benchmarks",),
                section_order=1,
            ),
            RetrievalOutlineSection(
                section_id="s2",
                title="Challenges",
                goal="Describe remaining gaps.",
                suggested_evidence_themes=(),
                key_points=("robustness", "coverage"),
                section_order=2,
            ),
        ),
    )

    async with database_runtime.session_factory() as session:
        now = datetime.now(tz=UTC)
        session.add(
            ProjectRow(
                id=project_id,
                tenant_id=tenant_id,
                name="Project",
                description=None,
                created_by=str(user_id),
                created_at=now,
                updated_at=now,
            )
        )
        session.add(
            RunRow(
                id=run_id,
                tenant_id=tenant_id,
                project_id=project_id,
                conversation_id=None,
                created_by_user_id=user_id,
                status="running",
                current_stage="retrieve",
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
        repository = SqlAlchemyRetrievalIngestionRepository(
            session,
            embedding_model="text-embedding-3-small",
        )

        count = await repository.persist_selected_sources(run_id=run_id, outline=outline, selected=[])
        await session.commit()

        stored_outline = await session.scalar(
            select(RetrievalOutlineRow).where(RetrievalOutlineRow.run_id == run_id)
        )
        stored_sections = (
            await session.scalars(
                select(RetrievalOutlineSectionRow)
                .join(RetrievalOutlineRow, RetrievalOutlineSectionRow.outline_id == RetrievalOutlineRow.id)
                .where(RetrievalOutlineRow.run_id == run_id)
                .order_by(RetrievalOutlineSectionRow.section_order.asc())
            )
        ).all()

    assert count == 0
    assert stored_outline is not None
    assert stored_outline.report_title == "AI Safety Benchmarking Outlook"
    assert [(row.section_id, row.title, row.section_order) for row in stored_sections] == [
        ("s1", "Recent Developments", 1),
        ("s2", "Challenges", 2),
    ]
    assert [row.key_points_json for row in stored_sections] == [["benchmarks"], ["robustness", "coverage"]]
