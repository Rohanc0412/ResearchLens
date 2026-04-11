import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from researchlens.modules.runs.application.dto import ResumeState
from researchlens.modules.runs.application.ports import (
    RunCheckpointStore,
    RunEventStore,
    RunRepository,
    TransactionManager,
)
from researchlens.modules.runs.domain import (
    RUN_STAGE_SEQUENCE,
    Run,
    RunEventAudience,
    RunEventLevel,
    RunEventType,
    RunStage,
    RunStatus,
    RunTransitionRecord,
    ensure_run_transition_allowed,
)


class RunClock(Protocol):
    def now(self) -> datetime: ...


class UtcRunClock:
    def now(self) -> datetime:
        return datetime.now(tz=UTC)


class SleepStageExecutionController:
    def __init__(self, delay_ms: int) -> None:
        self._delay_ms = delay_ms

    async def before_stage(self, *, run: Run, stage: RunStage) -> None:
        if self._delay_ms > 0:
            await asyncio.sleep(self._delay_ms / 1000)

    async def after_stage(self, *, run: Run, stage: RunStage) -> None:
        return None


@dataclass(slots=True)
class RunExecutionMutations:
    run_repository: RunRepository
    event_store: RunEventStore
    checkpoint_store: RunCheckpointStore
    transaction_manager: TransactionManager
    clock: RunClock

    async def start_run(self, *, run: Run, stage: RunStage) -> Run:
        async with self.transaction_manager.boundary():
            locked_run = await self.run_repository.get_by_id_for_update(run_id=run.id)
            if locked_run is None or locked_run.status == RunStatus.RUNNING:
                return locked_run or run
            ensure_run_transition_allowed(current=locked_run.status, target=RunStatus.RUNNING)
            now = self.clock.now()
            updated_run = locked_run.replace_values(
                status=RunStatus.RUNNING,
                current_stage=stage,
                started_at=locked_run.started_at or now,
                updated_at=now,
            )
            updated_run = await self.run_repository.save(updated_run)
            await self.run_repository.add_transition(
                RunTransitionRecord(
                    id=uuid4(),
                    run_id=updated_run.id,
                    from_status=locked_run.status,
                    to_status=RunStatus.RUNNING,
                    changed_at=now,
                    reason="worker_start",
                )
            )
            await self.event_store.append(
                run_id=updated_run.id,
                event_type=RunEventType.RUN_RUNNING,
                audience=RunEventAudience.STATE,
                level=RunEventLevel.INFO,
                status=updated_run.status.value,
                stage=stage.value,
                message="Run started" if updated_run.retry_count == 0 else "Retry started",
                payload_json={"attempt": updated_run.retry_count + 1},
                retry_count=updated_run.retry_count,
                cancel_requested=updated_run.cancel_requested_at is not None,
                created_at=now,
                event_key=f"run-running:{updated_run.retry_count}",
            )
            return updated_run

    async def append_stage_started(self, *, run: Run, stage: RunStage) -> None:
        async with self.transaction_manager.boundary():
            locked_run = await self.run_repository.get_by_id_for_update(run_id=run.id) or run
            await self.event_store.append(
                run_id=locked_run.id,
                event_type=RunEventType.STAGE_STARTED,
                audience=RunEventAudience.PROGRESS,
                level=RunEventLevel.INFO,
                status=locked_run.status.value,
                stage=stage.value,
                message=stage_started_message(stage),
                payload_json={"attempt": locked_run.retry_count + 1},
                retry_count=locked_run.retry_count,
                cancel_requested=locked_run.cancel_requested_at is not None,
                created_at=self.clock.now(),
                event_key=f"attempt-{locked_run.retry_count}:{stage.value}:started",
            )

    async def complete_stage(
        self,
        *,
        run: Run,
        stage: RunStage,
        resume_state: ResumeState,
    ) -> Run:
        next_stage = next_stage_after(stage)
        checkpoint_key = f"attempt-{run.retry_count}:{stage.value}:completed"
        now = self.clock.now()
        async with self.transaction_manager.boundary():
            locked_run = await self.run_repository.get_by_id_for_update(run_id=run.id) or run
            updated_run = await self._save_stage_progress(
                locked_run=locked_run,
                stage=stage,
                next_stage=next_stage,
                checkpoint_key=checkpoint_key,
                resume_state=resume_state,
                now=now,
            )
            return updated_run

    async def _save_stage_progress(
        self,
        *,
        locked_run: Run,
        stage: RunStage,
        next_stage: RunStage | None,
        checkpoint_key: str,
        resume_state: ResumeState,
        now: datetime,
    ) -> Run:
        updated_run = await self.run_repository.save(
            locked_run.replace_values(current_stage=next_stage or stage, updated_at=now)
        )
        await self._write_checkpoint(
            run=updated_run,
            stage=stage,
            next_stage=next_stage,
            checkpoint_key=checkpoint_key,
            resume_state=resume_state,
            now=now,
        )
        await self._append_stage_progress_events(
            run=updated_run,
            stage=stage,
            next_stage=next_stage,
            checkpoint_key=checkpoint_key,
            now=now,
        )
        return updated_run

    async def _write_checkpoint(
        self,
        *,
        run: Run,
        stage: RunStage,
        next_stage: RunStage | None,
        checkpoint_key: str,
        resume_state: ResumeState,
        now: datetime,
    ) -> None:
        completed_stages = [
            *(_stage.value for _stage in resume_state.completed_stages),
            stage.value,
        ]
        await self.checkpoint_store.append(
            run_id=run.id,
            stage=stage,
            checkpoint_key=checkpoint_key,
            payload_json={
                "attempt": run.retry_count + 1,
                "completed_stages": completed_stages,
                "next_stage": next_stage.value if next_stage else None,
            },
            summary_json={
                "current_stage": stage.value,
                "next_stage": next_stage.value if next_stage else None,
                "retry_count": run.retry_count,
            },
            created_at=now,
        )

    async def _append_stage_progress_events(
        self,
        *,
        run: Run,
        stage: RunStage,
        next_stage: RunStage | None,
        checkpoint_key: str,
        now: datetime,
    ) -> None:
        await self.event_store.append(
            run_id=run.id,
            event_type=RunEventType.CHECKPOINT_WRITTEN,
            audience=RunEventAudience.PROGRESS,
            level=RunEventLevel.INFO,
            status=run.status.value,
            stage=stage.value,
            message="Progress saved",
            payload_json={
                "checkpoint_key": checkpoint_key,
                "next_stage": next_stage.value if next_stage else None,
            },
            retry_count=run.retry_count,
            cancel_requested=run.cancel_requested_at is not None,
            created_at=now,
            event_key=f"{checkpoint_key}:event",
        )
        await self.event_store.append(
            run_id=run.id,
            event_type=RunEventType.STAGE_COMPLETED,
            audience=RunEventAudience.PROGRESS,
            level=RunEventLevel.INFO,
            status=run.status.value,
            stage=stage.value,
            message=stage_completed_message(stage),
            payload_json=None,
            retry_count=run.retry_count,
            cancel_requested=run.cancel_requested_at is not None,
            created_at=now,
            event_key=f"attempt-{run.retry_count}:{stage.value}:completed",
        )

    async def load_resume_state(self, run: Run) -> ResumeState:
        latest_checkpoint = await self.checkpoint_store.latest_for_run(run_id=run.id)
        if latest_checkpoint is None:
            return ResumeState(
                start_stage=run.current_stage or RunStage.RETRIEVE,
                completed_stages=tuple(),
                latest_checkpoint=None,
            )
        payload = latest_checkpoint.payload_json or {}
        completed = tuple(RunStage(value) for value in payload.get("completed_stages", []))
        next_stage_value = payload.get("next_stage")
        start_stage = RunStage(next_stage_value) if next_stage_value else latest_checkpoint.stage
        return ResumeState(
            start_stage=start_stage,
            completed_stages=completed,
            latest_checkpoint=latest_checkpoint,
        )


def next_stage_after(stage: RunStage) -> RunStage | None:
    current_index = RUN_STAGE_SEQUENCE.index(stage)
    if current_index == len(RUN_STAGE_SEQUENCE) - 1:
        return None
    return RUN_STAGE_SEQUENCE[current_index + 1]


def stage_started_message(stage: RunStage) -> str:
    if stage == RunStage.RETRIEVE:
        return "Searching for relevant sources"
    if stage == RunStage.DRAFT:
        return "Drafting report"
    if stage == RunStage.EVALUATE:
        return "Checking quality"
    return "Exporting result"


def stage_completed_message(stage: RunStage) -> str:
    if stage == RunStage.RETRIEVE:
        return "Source search complete"
    if stage == RunStage.DRAFT:
        return "Drafting complete"
    if stage == RunStage.EVALUATE:
        return "Quality check complete"
    return "Export complete"
