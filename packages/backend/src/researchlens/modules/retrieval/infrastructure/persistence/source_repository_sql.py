from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.retrieval.application.ports import RetrievalIngestionRepository
from researchlens.modules.retrieval.domain.ranking_policy import RankedCandidate
from researchlens.modules.retrieval.infrastructure.ingestion.content_selection import (
    choose_ingestible_content,
)
from researchlens.modules.retrieval.infrastructure.persistence.rows import (
    RetrievalChunkEmbeddingRow,
    RetrievalSourceChunkRow,
    RetrievalSourceRow,
    RetrievalSourceSnapshotRow,
    RunRetrievalSourceRow,
)
from researchlens.shared.embeddings.domain import EmbeddingRequest
from researchlens.shared.embeddings.ports import EmbeddingClient


class SqlAlchemyRetrievalIngestionRepository(RetrievalIngestionRepository):
    def __init__(
        self,
        session: AsyncSession,
        *,
        embedding_model: str,
        embedding_client: EmbeddingClient | None = None,
    ) -> None:
        self._session = session
        self._embedding_model = embedding_model
        self._embedding_client = embedding_client

    async def persist_selected_sources(
        self,
        *,
        run_id: UUID,
        selected: list[RankedCandidate],
    ) -> int:
        count = 0
        for rank, item in enumerate(selected, start=1):
            source_id = await self._upsert_source(item)
            snapshot_id = await self._upsert_snapshot(source_id=source_id, item=item)
            if snapshot_id is not None:
                await self._insert_chunks(snapshot_id=snapshot_id, item=item)
            await self._link_run_source(run_id=run_id, source_id=source_id, rank=rank, item=item)
            count += 1
        await self._session.flush()
        return count

    async def _upsert_source(self, item: RankedCandidate) -> UUID:
        candidate = item.candidate
        key = candidate.identifiers.canonical_key(candidate.title)
        existing = await self._session.scalar(
            select(RetrievalSourceRow).where(RetrievalSourceRow.canonical_key == key)
        )
        now = datetime.now(tz=UTC)
        if existing is not None:
            existing.updated_at = now
            return existing.id
        row = RetrievalSourceRow(
            id=uuid4(),
            canonical_key=key,
            provider_name=candidate.provider_name,
            provider_record_id=candidate.provider_record_id,
            title=candidate.title,
            identifiers_json=asdict(candidate.identifiers),
            metadata_json={"provenance": [asdict(item) for item in candidate.provenance]},
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.flush()
        return row.id

    async def _upsert_snapshot(self, *, source_id: UUID, item: RankedCandidate) -> UUID | None:
        content = choose_ingestible_content(
            title=item.candidate.title,
            abstract=item.candidate.abstract,
            full_text=item.candidate.full_text,
        )
        existing = await self._session.scalar(
            select(RetrievalSourceSnapshotRow).where(
                RetrievalSourceSnapshotRow.source_id == source_id,
                RetrievalSourceSnapshotRow.content_hash == content.content_hash,
            )
        )
        if existing is not None:
            return None
        row = RetrievalSourceSnapshotRow(
            id=uuid4(),
            source_id=source_id,
            content_hash=content.content_hash,
            content_kind=content.content_kind,
            content_text=content.text,
            created_at=datetime.now(tz=UTC),
        )
        self._session.add(row)
        await self._session.flush()
        return row.id

    async def _insert_chunks(self, *, snapshot_id: UUID, item: RankedCandidate) -> None:
        content = choose_ingestible_content(
            title=item.candidate.title,
            abstract=item.candidate.abstract,
            full_text=item.candidate.full_text,
        )
        chunk = content.text[:2000]
        text_hash = sha256(chunk.encode("utf-8")).hexdigest()
        chunk_row = RetrievalSourceChunkRow(
            id=uuid4(),
            snapshot_id=snapshot_id,
            chunk_index=0,
            text_hash=text_hash,
            text=chunk,
            created_at=datetime.now(tz=UTC),
        )
        self._session.add(chunk_row)
        await self._session.flush()
        existing_embedding = await self._session.scalar(
            select(RetrievalChunkEmbeddingRow).where(
                RetrievalChunkEmbeddingRow.text_hash == text_hash,
                RetrievalChunkEmbeddingRow.model == self._embedding_model,
            )
        )
        if existing_embedding is not None:
            return
        vector = []
        if self._embedding_client is not None:
            result = await self._embedding_client.embed(EmbeddingRequest(texts=(chunk,)))
            vector = list(result.vectors[0]) if result.vectors else []
        self._session.add(
            RetrievalChunkEmbeddingRow(
                id=uuid4(),
                chunk_id=chunk_row.id,
                text_hash=text_hash,
                model=self._embedding_model,
                embedding_json=vector,
                created_at=datetime.now(tz=UTC),
            )
        )

    async def _link_run_source(
        self,
        *,
        run_id: UUID,
        source_id: UUID,
        rank: int,
        item: RankedCandidate,
    ) -> None:
        existing = await self._session.scalar(
            select(RunRetrievalSourceRow).where(
                RunRetrievalSourceRow.run_id == run_id,
                RunRetrievalSourceRow.source_id == source_id,
            )
        )
        if existing is not None:
            return
        self._session.add(
            RunRetrievalSourceRow(
                id=uuid4(),
                run_id=run_id,
                source_id=source_id,
                target_section=item.candidate.query_provenance.target_section,
                query_intent=item.candidate.query_provenance.intent,
                rank=rank,
                score=item.score_breakdown.total,
                created_at=datetime.now(tz=UTC),
            )
        )
