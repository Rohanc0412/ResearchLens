from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.runs.application.dto import RunSummaryView, to_run_summary_view
from researchlens.modules.runs.application.ports import RunRepository
from researchlens.shared.errors import NotFoundError


@dataclass(frozen=True, slots=True)
class GetRunQuery:
    tenant_id: UUID
    run_id: UUID


class GetRunUseCase:
    def __init__(self, run_repository: RunRepository) -> None:
        self._run_repository = run_repository

    async def execute(self, query: GetRunQuery) -> RunSummaryView:
        run = await self._run_repository.get_by_id_for_tenant(
            tenant_id=query.tenant_id,
            run_id=query.run_id,
        )
        if run is None:
            raise NotFoundError("Run was not found.")
        return to_run_summary_view(run)
