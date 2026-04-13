from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from researchlens.modules.evidence.application import (
    GetChunkDetailUseCase,
    GetRunEvidenceSummaryUseCase,
    GetSectionEvidenceTraceUseCase,
    GetSourceDetailUseCase,
)
from researchlens.modules.evidence.infrastructure.evidence_queries_sql import (
    SqlAlchemyEvidenceQueries,
)


@dataclass(slots=True)
class EvidenceRequestContext:
    get_run_summary: GetRunEvidenceSummaryUseCase
    get_section_trace: GetSectionEvidenceTraceUseCase
    get_chunk_detail: GetChunkDetailUseCase
    get_source_detail: GetSourceDetailUseCase


class SqlAlchemyEvidenceRuntime:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @asynccontextmanager
    async def request_context(self) -> AsyncIterator[EvidenceRequestContext]:
        async with self._session_factory() as session:
            queries = SqlAlchemyEvidenceQueries(session)
            yield EvidenceRequestContext(
                get_run_summary=GetRunEvidenceSummaryUseCase(queries),
                get_section_trace=GetSectionEvidenceTraceUseCase(queries),
                get_chunk_detail=GetChunkDetailUseCase(queries),
                get_source_detail=GetSourceDetailUseCase(queries),
            )
