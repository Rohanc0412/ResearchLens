from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.runs.application.dto import RunEventView, to_run_event_view
from researchlens.modules.runs.application.ports import RunEventStore, RunRepository
from researchlens.shared.errors import NotFoundError


@dataclass(frozen=True, slots=True)
class ListRunEventsQuery:
    tenant_id: UUID
    run_id: UUID
    after_event_number: int | None = None


class ListRunEventsUseCase:
    def __init__(
        self,
        *,
        run_repository: RunRepository,
        event_store: RunEventStore,
    ) -> None:
        self._run_repository = run_repository
        self._event_store = event_store

    async def execute(self, query: ListRunEventsQuery) -> list[RunEventView]:
        run = await self._run_repository.get_by_id_for_tenant(
            tenant_id=query.tenant_id,
            run_id=query.run_id,
        )
        if run is None:
            raise NotFoundError("Run was not found.")
        events = await self._event_store.list_for_run(
            run_id=query.run_id,
            after_event_number=query.after_event_number,
        )
        return [to_run_event_view(event) for event in events]
