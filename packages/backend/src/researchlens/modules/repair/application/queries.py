from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.repair.application.dtos import RepairReadSummary
from researchlens.modules.repair.application.ports import RepairRepository


@dataclass(frozen=True, slots=True)
class LatestRepairSummaryQuery:
    tenant_id: UUID
    run_id: UUID


class GetLatestRepairSummaryUseCase:
    def __init__(self, repository: RepairRepository) -> None:
        self._repository = repository

    async def execute(self, query: LatestRepairSummaryQuery) -> RepairReadSummary | None:
        return await self._repository.latest_summary(
            tenant_id=query.tenant_id,
            run_id=query.run_id,
        )
