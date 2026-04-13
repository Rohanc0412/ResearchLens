from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.evidence.application.dtos import (
    ChunkDetail,
    RunEvidenceSummary,
    SectionEvidenceTrace,
    SourceDetail,
)
from researchlens.modules.evidence.application.ports import EvidenceQueries


@dataclass(frozen=True, slots=True)
class RunEvidenceQuery:
    tenant_id: UUID
    run_id: UUID


@dataclass(frozen=True, slots=True)
class SectionEvidenceQuery:
    tenant_id: UUID
    run_id: UUID
    section_id: str


@dataclass(frozen=True, slots=True)
class ChunkDetailQuery:
    tenant_id: UUID
    chunk_id: UUID
    context_window: int


@dataclass(frozen=True, slots=True)
class SourceDetailQuery:
    tenant_id: UUID
    source_id: UUID


class GetRunEvidenceSummaryUseCase:
    def __init__(self, queries: EvidenceQueries) -> None:
        self._queries = queries

    async def execute(self, query: RunEvidenceQuery) -> RunEvidenceSummary | None:
        return await self._queries.run_summary(tenant_id=query.tenant_id, run_id=query.run_id)


class GetSectionEvidenceTraceUseCase:
    def __init__(self, queries: EvidenceQueries) -> None:
        self._queries = queries

    async def execute(self, query: SectionEvidenceQuery) -> SectionEvidenceTrace | None:
        return await self._queries.section_trace(
            tenant_id=query.tenant_id,
            run_id=query.run_id,
            section_id=query.section_id,
        )


class GetChunkDetailUseCase:
    def __init__(self, queries: EvidenceQueries) -> None:
        self._queries = queries

    async def execute(self, query: ChunkDetailQuery) -> ChunkDetail | None:
        return await self._queries.chunk_detail(
            tenant_id=query.tenant_id,
            chunk_id=query.chunk_id,
            context_window=query.context_window,
        )


class GetSourceDetailUseCase:
    def __init__(self, queries: EvidenceQueries) -> None:
        self._queries = queries

    async def execute(self, query: SourceDetailQuery) -> SourceDetail | None:
        return await self._queries.source_detail(
            tenant_id=query.tenant_id,
            source_id=query.source_id,
        )
