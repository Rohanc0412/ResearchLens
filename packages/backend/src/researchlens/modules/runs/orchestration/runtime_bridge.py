from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from researchlens.modules.runs.application.dto import ResumeState
from researchlens.modules.runs.application.ports import (
    RunCheckpointStore,
    RunEventStore,
    RunQueueBackend,
    RunRepository,
    TransactionManager,
)
from researchlens.modules.runs.application.run_clock import RunClock
from researchlens.modules.runs.application.run_execution_support import (
    RunExecutionMutations,
)
from researchlens.modules.runs.application.run_terminal_mutations import RunTerminalMutations
from researchlens.modules.runs.domain import (
    Run,
    RunCheckpointRecord,
    RunEventType,
    RunStage,
    RunStatus,
)
from researchlens.modules.runs.orchestration.checkpoint_bridge import (
    RunGraphCheckpointBridge,
)
from researchlens.modules.runs.orchestration.event_bridge import RunGraphEventBridge
from researchlens.modules.runs.orchestration.state import RunGraphState, checkpoint_stage_values


@dataclass(frozen=True, slots=True)
class RunContextSnapshot:
    run: Run
    request_text: str
    latest_checkpoint: RunCheckpointRecord | None


class RunGraphRuntimeBridge:
    def __init__(
        self,
        *,
        run_repository: RunRepository,
        event_store: RunEventStore,
        checkpoint_store: RunCheckpointStore,
        queue_backend: RunQueueBackend,
        transaction_manager: TransactionManager,
        clock: RunClock,
        queue_lease_seconds: int,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self._run_repository = run_repository
        self._event_store = event_store
        self._checkpoint_store = checkpoint_store
        self._queue_backend = queue_backend
        self._clock = clock
        self._queue_lease_seconds = queue_lease_seconds
        self._mutations = RunExecutionMutations(
            run_repository=run_repository,
            event_store=event_store,
            checkpoint_store=checkpoint_store,
            transaction_manager=transaction_manager,
            clock=clock,
        )
        self._terminal_mutations = RunTerminalMutations(
            run_repository=run_repository,
            event_store=event_store,
            transaction_manager=transaction_manager,
            clock=clock,
        )
        self._events = RunGraphEventBridge(
            event_store=event_store,
            transaction_manager=transaction_manager,
            clock=clock,
            session_factory=session_factory,
        )
        self._checkpoints = RunGraphCheckpointBridge(
            checkpoint_store=checkpoint_store,
            transaction_manager=transaction_manager,
            clock=clock,
            session_factory=session_factory,
        )

    async def load_context(self, *, run_id: UUID) -> RunContextSnapshot:
        run = await self._run_repository.get_by_id(run_id=run_id)
        if run is None:
            raise ValueError(f"Unknown run {run_id}")
        latest_checkpoint = await self._checkpoint_store.latest_for_run(run_id=run_id)
        request_text = await self._request_text_for_run(
            run_id=run_id,
            output_type=run.output_type,
        )
        return RunContextSnapshot(
            run=run,
            request_text=request_text,
            latest_checkpoint=latest_checkpoint,
        )

    async def mark_running(self, *, run: Run, start_stage: RunStage) -> Run:
        if run.status != RunStatus.QUEUED:
            return run
        return await self._mutations.start_run(run=run, stage=start_stage)

    async def stage_entered(
        self,
        *,
        state: RunGraphState,
        stage: RunStage,
    ) -> bool:
        run = await self._run_repository.get_by_id_for_update(run_id=UUID(str(state["run_id"])))
        if run is None:
            return False
        if run.cancel_requested_at is not None:
            state["cancel_requested"] = True
            state["terminal_status"] = "canceled"
            return False
        await self._mutations.append_stage_started(run=run, stage=stage)
        await self._queue_backend.heartbeat(
            queue_item_id=UUID(str(state["queue_item_id"])),
            lease_token=UUID(str(state["lease_token"])),
            lease_expires_at=self._clock.now() + timedelta(seconds=self._queue_lease_seconds),
        )
        return True

    async def stage_completed(
        self,
        *,
        state: RunGraphState,
        stage: RunStage,
    ) -> None:
        run = await self._run_repository.get_by_id_for_update(run_id=UUID(str(state["run_id"])))
        if run is None:
            return
        updated_run = await self._mutations.complete_stage(
            run=run,
            stage=stage,
            resume_state=ResumeState(
                start_stage=RunStage(str(state["start_stage"])),
                completed_stages=checkpoint_stage_values(state),
                latest_checkpoint=await self._checkpoint_store.latest_for_run(run_id=run.id),
            ),
        )
        completed_stages = tuple((*state["completed_stages"], stage.value))
        state["completed_stages"] = completed_stages
        state["current_stage"] = (
            updated_run.current_stage.value if updated_run.current_stage else None
        )
        latest = await self._checkpoint_store.latest_for_run(run_id=updated_run.id)
        state["latest_checkpoint_key"] = latest.checkpoint_key if latest else None
        state["latest_checkpoint_stage"] = latest.stage.value if latest else None

    async def finalize(self, *, state: RunGraphState) -> None:
        run = await self._run_repository.get_by_id_for_update(run_id=UUID(str(state["run_id"])))
        if run is None:
            return
        if state.get("terminal_status") == "canceled" or run.cancel_requested_at is not None:
            await self._terminal_mutations.finalize_cancel(run=run)
            return
        await self._terminal_mutations.finalize_success(run=run)

    def stage_event_sink(self, *, state: RunGraphState, stage: RunStage) -> "_StageEventSink":
        return _StageEventSink(bridge=self._events, state=state, stage=stage)

    def stage_checkpoint_sink(
        self,
        *,
        state: RunGraphState,
        stage: RunStage,
    ) -> "_StageCheckpointSink":
        return _StageCheckpointSink(bridge=self._checkpoints, state=state, stage=stage)

    async def _request_text_for_run(self, *, run_id: UUID, output_type: str) -> str:
        events = await self._event_store.list_for_run(run_id=run_id, after_event_number=None)
        for event in events:
            if event.event_type == RunEventType.RUN_CREATED and event.payload_json:
                request_text = event.payload_json.get("request_text")
                if isinstance(request_text, str) and request_text.strip():
                    return request_text
        return f"{output_type} run {run_id}"


class _StageEventSink:
    def __init__(
        self,
        *,
        bridge: RunGraphEventBridge,
        state: RunGraphState,
        stage: RunStage,
    ) -> None:
        self._bridge = bridge
        self._state = state
        self._stage = stage

    async def info(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        await self._bridge.info(
            run_id=UUID(str(self._state["run_id"])),
            retry_count=int(self._state["retry_count"]),
            cancel_requested=bool(self._state["cancel_requested"]),
            stage=self._stage,
            key=key,
            message=message,
            payload=payload,
        )

    async def warning(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        await self._bridge.warning(
            run_id=UUID(str(self._state["run_id"])),
            retry_count=int(self._state["retry_count"]),
            cancel_requested=bool(self._state["cancel_requested"]),
            stage=self._stage,
            key=key,
            message=message,
            payload=payload,
        )


class _StageCheckpointSink:
    def __init__(
        self,
        *,
        bridge: RunGraphCheckpointBridge,
        state: RunGraphState,
        stage: RunStage,
    ) -> None:
        self._bridge = bridge
        self._state = state
        self._stage = stage

    async def checkpoint(
        self,
        *,
        key: str,
        summary: dict[str, object],
        completed_stages: tuple[str, ...],
        next_stage: str | None,
    ) -> None:
        await self._bridge.checkpoint(
            run_id=UUID(str(self._state["run_id"])),
            retry_count=int(self._state["retry_count"]),
            stage=self._stage,
            key=key,
            summary=summary,
            completed_stages=completed_stages,
            next_stage=next_stage,
        )
