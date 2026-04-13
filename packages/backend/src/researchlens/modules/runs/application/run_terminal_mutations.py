from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

from researchlens.modules.runs.application.ports import (
    RunEventStore,
    RunRepository,
    TransactionManager,
)
from researchlens.modules.runs.application.run_clock import RunClock
from researchlens.modules.runs.domain import (
    Run,
    RunEventAudience,
    RunEventLevel,
    RunEventType,
    RunStage,
    RunStatus,
    RunTransitionRecord,
    ensure_run_transition_allowed,
)


@dataclass(slots=True)
class RunTerminalMutations:
    run_repository: RunRepository
    event_store: RunEventStore
    transaction_manager: TransactionManager
    clock: RunClock

    async def finalize_success(self, *, run: Run) -> None:
        await self._finalize_terminal(
            run=run,
            target_status=RunStatus.SUCCEEDED,
            reason="complete",
            event_type=RunEventType.RUN_SUCCEEDED,
            message="Run completed successfully",
            payload_json=None,
            error=False,
        )

    async def finalize_cancel(self, *, run: Run) -> None:
        await self._finalize_terminal(
            run=run,
            target_status=RunStatus.CANCELED,
            reason="cancel",
            event_type=RunEventType.RUN_CANCELED,
            message="Run stopped",
            payload_json=None,
            error=False,
        )

    async def finalize_failure(
        self,
        *,
        run: Run,
        reason: str,
        error_code: str,
    ) -> None:
        async with self.transaction_manager.boundary():
            locked_run = await self.run_repository.get_by_id_for_update(run_id=run.id) or run
            if locked_run.status == RunStatus.FAILED:
                return
            ensure_run_transition_allowed(current=locked_run.status, target=RunStatus.FAILED)
            now = self.clock.now()
            updated_run = locked_run.replace_values(
                status=RunStatus.FAILED,
                finished_at=now,
                failure_reason=reason,
                error_code=error_code,
                updated_at=now,
            )
            updated_run = await self.run_repository.save(updated_run)
            await self.run_repository.add_transition(
                RunTransitionRecord(
                    id=uuid4(),
                    run_id=updated_run.id,
                    from_status=locked_run.status,
                    to_status=RunStatus.FAILED,
                    changed_at=now,
                    reason="failure",
                )
            )
            message = (
                "Run failed before processing started"
                if locked_run.status == RunStatus.QUEUED
                else "Run failed during processing"
            )
            for event_type in (RunEventType.STAGE_FAILED, RunEventType.RUN_FAILED):
                await self.event_store.append(
                    run_id=updated_run.id,
                    event_type=event_type,
                    audience=RunEventAudience.PROGRESS
                    if event_type == RunEventType.STAGE_FAILED
                    else RunEventAudience.STATE,
                    level=RunEventLevel.ERROR,
                    status=updated_run.status.value,
                    stage=updated_run.current_stage.value if updated_run.current_stage else None,
                    message=message,
                    payload_json={"error_code": error_code},
                    retry_count=updated_run.retry_count,
                    cancel_requested=updated_run.cancel_requested_at is not None,
                    created_at=now,
                    event_key=f"{event_type.value}:{updated_run.retry_count}",
                )

    async def _finalize_terminal(
        self,
        *,
        run: Run,
        target_status: RunStatus,
        reason: str,
        event_type: RunEventType,
        message: str,
        payload_json: dict[str, Any] | None,
        error: bool,
    ) -> None:
        async with self.transaction_manager.boundary():
            locked_run = await self.run_repository.get_by_id_for_update(run_id=run.id) or run
            if locked_run.status == target_status:
                return
            ensure_run_transition_allowed(current=locked_run.status, target=target_status)
            now = self.clock.now()
            updated_run = self._build_terminal_run(
                locked_run=locked_run,
                target_status=target_status,
                finished_at=now,
            )
            updated_run = await self.run_repository.save(updated_run)
            await self.run_repository.add_transition(
                RunTransitionRecord(
                    id=uuid4(),
                    run_id=updated_run.id,
                    from_status=locked_run.status,
                    to_status=target_status,
                    changed_at=now,
                    reason=reason,
                )
            )
            await self.event_store.append(
                run_id=updated_run.id,
                event_type=event_type,
                audience=RunEventAudience.STATE,
                level=RunEventLevel.ERROR if error else RunEventLevel.INFO,
                status=updated_run.status.value,
                stage=updated_run.current_stage.value if updated_run.current_stage else None,
                message=message,
                payload_json=payload_json,
                retry_count=updated_run.retry_count,
                cancel_requested=updated_run.cancel_requested_at is not None,
                created_at=now,
                event_key=f"{event_type.value}:{updated_run.retry_count}",
            )

    def _build_terminal_run(
        self,
        *,
        locked_run: Run,
        target_status: RunStatus,
        finished_at: datetime,
    ) -> Run:
        if target_status == RunStatus.SUCCEEDED:
            return locked_run.replace_values(
                status=target_status,
                finished_at=finished_at,
                current_stage=RunStage.EXPORT,
                updated_at=finished_at,
            )
        return locked_run.replace_values(
            status=target_status,
            finished_at=finished_at,
            updated_at=finished_at,
        )
