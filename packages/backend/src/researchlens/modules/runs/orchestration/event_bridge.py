from uuid import UUID

from researchlens.modules.runs.application.ports import RunEventStore, TransactionManager
from researchlens.modules.runs.application.run_clock import RunClock
from researchlens.modules.runs.domain import (
    RunEventAudience,
    RunEventLevel,
    RunEventType,
    RunStage,
)


class RunGraphEventBridge:
    def __init__(
        self,
        *,
        event_store: RunEventStore,
        transaction_manager: TransactionManager,
        clock: RunClock,
    ) -> None:
        self._event_store = event_store
        self._transaction_manager = transaction_manager
        self._clock = clock

    async def info(
        self,
        *,
        run_id: UUID,
        retry_count: int,
        cancel_requested: bool,
        stage: RunStage,
        key: str,
        message: str,
        payload: dict[str, object],
    ) -> None:
        await self._append(
            run_id=run_id,
            retry_count=retry_count,
            cancel_requested=cancel_requested,
            stage=stage,
            key=key,
            level=RunEventLevel.INFO,
            message=message,
            payload=payload,
        )

    async def warning(
        self,
        *,
        run_id: UUID,
        retry_count: int,
        cancel_requested: bool,
        stage: RunStage,
        key: str,
        message: str,
        payload: dict[str, object],
    ) -> None:
        await self._append(
            run_id=run_id,
            retry_count=retry_count,
            cancel_requested=cancel_requested,
            stage=stage,
            key=key,
            level=RunEventLevel.WARN,
            message=message,
            payload=payload,
        )

    async def _append(
        self,
        *,
        run_id: UUID,
        retry_count: int,
        cancel_requested: bool,
        stage: RunStage,
        key: str,
        level: RunEventLevel,
        message: str,
        payload: dict[str, object],
    ) -> None:
        async with self._transaction_manager.boundary():
            await self._event_store.append(
                run_id=run_id,
                event_type=RunEventType.CHECKPOINT_WRITTEN,
                audience=RunEventAudience.PROGRESS,
                level=level,
                status="running",
                stage=stage.value,
                message=message,
                payload_json=payload,
                retry_count=retry_count,
                cancel_requested=cancel_requested,
                created_at=self._clock.now(),
                event_key=f"attempt-{retry_count}:{key}",
            )
