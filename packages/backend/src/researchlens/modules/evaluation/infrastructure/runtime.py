from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from researchlens.modules.evaluation.application import (
    GetLatestEvaluationSummaryUseCase,
    ListEvaluationIssuesUseCase,
    LoadRepairCandidatesUseCase,
)
from researchlens.modules.evaluation.infrastructure.repositories import (
    SqlAlchemyEvaluationRepository,
)


@dataclass(slots=True)
class EvaluationRequestContext:
    get_latest_summary: GetLatestEvaluationSummaryUseCase
    list_issues: ListEvaluationIssuesUseCase
    load_repair_candidates: LoadRepairCandidatesUseCase


class SqlAlchemyEvaluationRuntime:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @asynccontextmanager
    async def request_context(self) -> AsyncIterator[EvaluationRequestContext]:
        async with self._session_factory() as session:
            repository = SqlAlchemyEvaluationRepository(session)
            yield EvaluationRequestContext(
                get_latest_summary=GetLatestEvaluationSummaryUseCase(repository),
                list_issues=ListEvaluationIssuesUseCase(repository),
                load_repair_candidates=LoadRepairCandidatesUseCase(repository),
            )
