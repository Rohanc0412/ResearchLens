from datetime import UTC, datetime

from researchlens.modules.runs.application.ports import RunCheckpointStore, RunEventStore
from researchlens.modules.runs.domain import (
    Run,
    RunEventAudience,
    RunEventLevel,
    RunEventType,
    RunStage,
)
from researchlens.shared.db.transaction_manager import SqlAlchemyTransactionManager


class StageRunEventWriter:
    def __init__(
        self,
        *,
        run: Run,
        event_store: RunEventStore,
        transaction_manager: SqlAlchemyTransactionManager,
        stage: RunStage,
    ) -> None:
        self._run = run
        self._event_store = event_store
        self._transaction_manager = transaction_manager
        self._stage = stage

    async def info(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        await self._append(key=key, level=RunEventLevel.INFO, message=message, payload=payload)

    async def warning(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        await self._append(key=key, level=RunEventLevel.WARN, message=message, payload=payload)

    async def _append(
        self,
        *,
        key: str,
        level: RunEventLevel,
        message: str,
        payload: dict[str, object],
    ) -> None:
        async with self._transaction_manager.boundary():
            await self._event_store.append(
                run_id=self._run.id,
                event_type=RunEventType.CHECKPOINT_WRITTEN,
                audience=RunEventAudience.PROGRESS,
                level=level,
                status=self._run.status.value,
                stage=self._stage.value,
                message=message,
                payload_json=payload,
                retry_count=self._run.retry_count,
                cancel_requested=self._run.cancel_requested_at is not None,
                created_at=datetime.now(tz=UTC),
                event_key=f"attempt-{self._run.retry_count}:{key}",
            )


class StageRunCheckpointWriter:
    def __init__(
        self,
        *,
        run: Run,
        checkpoint_store: RunCheckpointStore,
        transaction_manager: SqlAlchemyTransactionManager,
        stage: RunStage,
    ) -> None:
        self._run = run
        self._checkpoint_store = checkpoint_store
        self._transaction_manager = transaction_manager
        self._stage = stage

    async def checkpoint(self, *, key: str, summary: dict[str, object]) -> None:
        async with self._transaction_manager.boundary():
            await self._checkpoint_store.append(
                run_id=self._run.id,
                stage=self._stage,
                checkpoint_key=f"attempt-{self._run.retry_count}:{key}",
                payload_json=summary,
                summary_json=summary,
                created_at=datetime.now(tz=UTC),
            )
