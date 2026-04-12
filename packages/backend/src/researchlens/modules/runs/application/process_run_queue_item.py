from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.runs.application.ports import (
    RunEventStore,
    RunExecutionOrchestrator,
    RunQueueBackend,
    RunRepository,
    TransactionManager,
)
from researchlens.modules.runs.application.run_clock import RunClock, UtcRunClock
from researchlens.modules.runs.application.run_terminal_mutations import RunTerminalMutations
from researchlens.modules.runs.domain import TERMINAL_RUN_STATUSES


@dataclass(frozen=True, slots=True)
class ProcessRunQueueItemCommand:
    queue_item_id: UUID
    lease_token: UUID
    run_id: UUID


class ProcessRunQueueItemUseCase:
    def __init__(
        self,
        *,
        run_repository: RunRepository,
        event_store: RunEventStore,
        queue_backend: RunQueueBackend,
        transaction_manager: TransactionManager,
        run_orchestrator: RunExecutionOrchestrator,
        clock: RunClock | None = None,
    ) -> None:
        self._run_repository = run_repository
        self._queue_backend = queue_backend
        self._run_orchestrator = run_orchestrator
        self._clock = clock or UtcRunClock()
        self._terminal_mutations = RunTerminalMutations(
            run_repository=run_repository,
            event_store=event_store,
            transaction_manager=transaction_manager,
            clock=self._clock,
        )

    async def execute(self, command: ProcessRunQueueItemCommand) -> None:
        run = await self._run_repository.get_by_id(run_id=command.run_id)
        if run is None or run.status in TERMINAL_RUN_STATUSES:
            await self._ack_queue_item(command)
            return

        try:
            await self._run_orchestrator.execute(
                run=run,
                queue_item_id=command.queue_item_id,
                lease_token=command.lease_token,
            )
        except Exception as exc:
            run = await self._run_repository.get_by_id(run_id=command.run_id) or run
            await self._terminal_mutations.finalize_failure(
                run=run,
                reason=str(exc),
                error_code=type(exc).__name__,
            )
        await self._ack_queue_item(command)

    async def _ack_queue_item(self, command: ProcessRunQueueItemCommand) -> None:
        await self._queue_backend.complete(
            queue_item_id=command.queue_item_id,
            lease_token=command.lease_token,
            completed_at=self._clock.now(),
        )
