from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from researchlens.modules.runs.application.ports import (
    RunCheckpointStore,
    RunEventStore,
    RunQueueBackend,
    RunRepository,
    StageExecutionController,
    TransactionManager,
)
from researchlens.modules.runs.application.run_execution_support import (
    RunClock,
    RunExecutionMutations,
    UtcRunClock,
)
from researchlens.modules.runs.application.run_terminal_mutations import RunTerminalMutations
from researchlens.modules.runs.domain import RUN_STAGE_SEQUENCE, TERMINAL_RUN_STATUSES, RunStatus


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
        checkpoint_store: RunCheckpointStore,
        queue_backend: RunQueueBackend,
        transaction_manager: TransactionManager,
        stage_controller: StageExecutionController,
        queue_lease_seconds: int,
        clock: RunClock | None = None,
    ) -> None:
        self._run_repository = run_repository
        self._queue_backend = queue_backend
        self._stage_controller = stage_controller
        self._queue_lease_seconds = queue_lease_seconds
        self._clock = clock or UtcRunClock()
        self._mutations = RunExecutionMutations(
            run_repository=run_repository,
            event_store=event_store,
            checkpoint_store=checkpoint_store,
            transaction_manager=transaction_manager,
            clock=self._clock,
        )
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

        resume_state = await self._mutations.load_resume_state(run)
        try:
            if run.status == RunStatus.QUEUED:
                run = await self._mutations.start_run(run=run, stage=resume_state.start_stage)

            for stage in RUN_STAGE_SEQUENCE[RUN_STAGE_SEQUENCE.index(resume_state.start_stage) :]:
                run = await self._run_repository.get_by_id_for_update(run_id=run.id) or run
                if run.cancel_requested_at is not None:
                    await self._terminal_mutations.finalize_cancel(run=run)
                    await self._ack_queue_item(command)
                    return
                await self._mutations.append_stage_started(run=run, stage=stage)
                await self._queue_backend.heartbeat(
                    queue_item_id=command.queue_item_id,
                    lease_token=command.lease_token,
                    lease_expires_at=self._clock.now()
                    + timedelta(seconds=self._queue_lease_seconds),
                )
                await self._stage_controller.before_stage(run=run, stage=stage)
                run = await self._run_repository.get_by_id_for_update(run_id=run.id) or run
                run = await self._mutations.complete_stage(
                    run=run,
                    stage=stage,
                    resume_state=resume_state,
                )
                await self._stage_controller.after_stage(run=run, stage=stage)

            run = await self._run_repository.get_by_id_for_update(run_id=run.id) or run
            if run.cancel_requested_at is not None:
                await self._terminal_mutations.finalize_cancel(run=run)
            else:
                await self._terminal_mutations.finalize_success(run=run)
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
