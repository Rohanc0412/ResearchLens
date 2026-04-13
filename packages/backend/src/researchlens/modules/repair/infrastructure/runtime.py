from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from researchlens.modules.repair.application import GetLatestRepairSummaryUseCase
from researchlens.modules.repair.infrastructure.repair_repository_sql import (
    SqlAlchemyRepairRepository,
)


@dataclass(slots=True)
class RepairRequestContext:
    get_latest_summary: GetLatestRepairSummaryUseCase


class SqlAlchemyRepairRuntime:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @asynccontextmanager
    async def request_context(self) -> AsyncIterator[RepairRequestContext]:
        async with self._session_factory() as session:
            repository = SqlAlchemyRepairRepository(session)
            yield RepairRequestContext(
                get_latest_summary=GetLatestRepairSummaryUseCase(repository),
            )
