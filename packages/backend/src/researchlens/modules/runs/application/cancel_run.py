from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from researchlens.modules.runs.application.dto import RunSummaryView, to_run_summary_view
from researchlens.modules.runs.application.ports import (
    RunEventStore,
    RunQueueBackend,
    RunRepository,
    TransactionManager,
)
from researchlens.modules.runs.domain import (
    Run,
    RunEventAudience,
    RunEventLevel,
    RunEventType,
    RunStatus,
    RunTransitionRecord,
    ensure_run_transition_allowed,
)
from researchlens.shared.errors import NotFoundError


@dataclass(frozen=True, slots=True)
class CancelRunCommand:
    tenant_id: UUID
    run_id: UUID


class CancelRunUseCase:
    def __init__(
        self,
        *,
        run_repository: RunRepository,
        event_store: RunEventStore,
        queue_backend: RunQueueBackend,
        transaction_manager: TransactionManager,
    ) -> None:
        self._run_repository = run_repository
        self._event_store = event_store
        self._queue_backend = queue_backend
        self._transaction_manager = transaction_manager

    async def execute(self, command: CancelRunCommand) -> RunSummaryView:
        async with self._transaction_manager.boundary():
            run = await self._require_run(command)
            if self._is_terminal(run):
                return to_run_summary_view(run)
            now = datetime.now(tz=UTC)
            if run.status == RunStatus.QUEUED:
                return await self._cancel_queued_run(run=run, now=now)
            if run.cancel_requested_at is not None:
                return to_run_summary_view(run)
            return await self._mark_running_cancel_requested(run=run, now=now)

    async def _require_run(self, command: CancelRunCommand) -> Run:
        run = await self._run_repository.get_by_id_for_tenant(
            tenant_id=command.tenant_id,
            run_id=command.run_id,
        )
        if run is None:
            raise NotFoundError("Run was not found.")
        return run

    def _is_terminal(self, run: Run) -> bool:
        return run.status in {RunStatus.CANCELED, RunStatus.SUCCEEDED, RunStatus.FAILED}

    async def _cancel_queued_run(self, *, run: Run, now: datetime) -> RunSummaryView:
        ensure_run_transition_allowed(current=run.status, target=RunStatus.CANCELED)
        updated_run = await self._run_repository.save(
            run.replace_values(
                status=RunStatus.CANCELED,
                cancel_requested_at=now,
                finished_at=now,
                updated_at=now,
            )
        )
        await self._run_repository.add_transition(
            RunTransitionRecord(
                id=uuid4(),
                run_id=run.id,
                from_status=run.status,
                to_status=RunStatus.CANCELED,
                changed_at=now,
                reason="cancel",
            )
        )
        await self._queue_backend.cancel_active_for_run(run_id=run.id, canceled_at=now)
        await self._append_cancel_events(
            run=run,
            updated_run=updated_run,
            now=now,
            stopped_before_start=True,
        )
        return to_run_summary_view(updated_run)

    async def _mark_running_cancel_requested(
        self,
        *,
        run: Run,
        now: datetime,
    ) -> RunSummaryView:
        updated_run = await self._run_repository.save(
            run.replace_values(cancel_requested_at=now, updated_at=now)
        )
        await self._event_store.append(
            run_id=run.id,
            event_type=RunEventType.CANCEL_REQUESTED,
            audience=RunEventAudience.STATE,
            level=RunEventLevel.INFO,
            status=updated_run.status.value,
            stage=updated_run.current_stage.value if updated_run.current_stage else None,
            message="Stopping after the current safe step",
            payload_json=None,
            retry_count=updated_run.retry_count,
            cancel_requested=True,
            created_at=now,
            event_key=f"cancel-requested:{updated_run.retry_count}",
        )
        return to_run_summary_view(updated_run)

    async def _append_cancel_events(
        self,
        *,
        run: Run,
        updated_run: Run,
        now: datetime,
        stopped_before_start: bool,
    ) -> None:
        message = "Run stopped before work began" if stopped_before_start else "Run stopped"
        stage = run.current_stage.value if run.current_stage else None
        await self._event_store.append(
            run_id=run.id,
            event_type=RunEventType.CANCEL_REQUESTED,
            audience=RunEventAudience.STATE,
            level=RunEventLevel.INFO,
            status=RunStatus.QUEUED.value,
            stage=stage,
            message=message,
            payload_json=None,
            retry_count=run.retry_count,
            cancel_requested=True,
            created_at=now,
            event_key=f"cancel-requested:{run.retry_count}",
        )
        await self._event_store.append(
            run_id=run.id,
            event_type=RunEventType.RUN_CANCELED,
            audience=RunEventAudience.STATE,
            level=RunEventLevel.INFO,
            status=RunStatus.CANCELED.value,
            stage=updated_run.current_stage.value if updated_run.current_stage else None,
            message=message,
            payload_json=None,
            retry_count=updated_run.retry_count,
            cancel_requested=True,
            created_at=now,
            event_key=f"run-canceled:{updated_run.retry_count}",
        )
