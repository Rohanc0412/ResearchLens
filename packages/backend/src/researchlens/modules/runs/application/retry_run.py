from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from researchlens.modules.runs.application.dto import (
    RetryDecision,
    RunSummaryView,
    to_run_summary_view,
)
from researchlens.modules.runs.application.ports import (
    RunCheckpointStore,
    RunEventStore,
    RunQueueBackend,
    RunRepository,
    TransactionManager,
)
from researchlens.modules.runs.application.retry_resume_policy import decide_retry_resume
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
class RetryRunCommand:
    tenant_id: UUID
    run_id: UUID


class RetryRunUseCase:
    def __init__(
        self,
        *,
        run_repository: RunRepository,
        event_store: RunEventStore,
        checkpoint_store: RunCheckpointStore,
        queue_backend: RunQueueBackend,
        transaction_manager: TransactionManager,
    ) -> None:
        self._run_repository = run_repository
        self._event_store = event_store
        self._checkpoint_store = checkpoint_store
        self._queue_backend = queue_backend
        self._transaction_manager = transaction_manager

    async def execute(self, command: RetryRunCommand) -> RunSummaryView:
        async with self._transaction_manager.boundary():
            run = await self._require_run(command)
            retry_decision = await self._build_retry_decision(run)
            now = datetime.now(tz=UTC)
            updated_run = await self._reset_run_for_retry(
                run=run,
                retry_decision=retry_decision,
                now=now,
            )
            await self._queue_backend.enqueue(
                tenant_id=updated_run.tenant_id,
                run_id=updated_run.id,
                available_at=now,
            )
            await self._append_retry_events(
                updated_run=updated_run,
                retry_decision=retry_decision,
                now=now,
            )
            return to_run_summary_view(updated_run)

    async def _require_run(self, command: RetryRunCommand) -> Run:
        run = await self._run_repository.get_by_id_for_tenant(
            tenant_id=command.tenant_id,
            run_id=command.run_id,
        )
        if run is None:
            raise NotFoundError("Run was not found.")
        ensure_run_transition_allowed(current=run.status, target=RunStatus.QUEUED)
        return run

    async def _build_retry_decision(self, run: Run) -> RetryDecision:
        latest_checkpoint = await self._checkpoint_store.latest_for_run(run_id=run.id)
        return decide_retry_resume(run=run, latest_checkpoint=latest_checkpoint)

    async def _reset_run_for_retry(
        self,
        *,
        run: Run,
        retry_decision: RetryDecision,
        now: datetime,
    ) -> Run:
        updated_run = await self._run_repository.save(
            run.replace_values(
                status=RunStatus.QUEUED,
                current_stage=retry_decision.resume_from_stage,
                retry_count=run.retry_count + 1,
                cancel_requested_at=None,
                started_at=None,
                finished_at=None,
                failure_reason=None,
                error_code=None,
                updated_at=now,
            )
        )
        await self._run_repository.add_transition(
            RunTransitionRecord(
                id=uuid4(),
                run_id=run.id,
                from_status=RunStatus.FAILED,
                to_status=RunStatus.QUEUED,
                changed_at=now,
                reason="retry",
            )
        )
        return updated_run

    async def _append_retry_events(
        self,
        *,
        updated_run: Run,
        retry_decision: RetryDecision,
        now: datetime,
    ) -> None:
        stage = updated_run.current_stage.value if updated_run.current_stage else None
        await self._event_store.append(
            run_id=updated_run.id,
            event_type=RunEventType.RETRY_REQUESTED,
            audience=RunEventAudience.STATE,
            level=RunEventLevel.INFO,
            status=updated_run.status.value,
            stage=stage,
            message=retry_decision.message,
            payload_json=retry_decision.payload,
            retry_count=updated_run.retry_count,
            cancel_requested=False,
            created_at=now,
            event_key=f"retry-requested:{updated_run.retry_count}",
        )
        await self._event_store.append(
            run_id=updated_run.id,
            event_type=RunEventType.RUN_QUEUED,
            audience=RunEventAudience.STATE,
            level=RunEventLevel.INFO,
            status=updated_run.status.value,
            stage=stage,
            message="Retry queued",
            payload_json=retry_decision.payload,
            retry_count=updated_run.retry_count,
            cancel_requested=False,
            created_at=now,
            event_key=f"run-queued:{updated_run.retry_count}",
        )
