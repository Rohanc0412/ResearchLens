import asyncio
from uuid import UUID

from researchlens.modules.runs.application.ports import RunCheckpointStore, TransactionManager
from researchlens.modules.runs.application.run_clock import RunClock
from researchlens.modules.runs.domain import RunStage


class RunGraphCheckpointBridge:
    def __init__(
        self,
        *,
        checkpoint_store: RunCheckpointStore,
        transaction_manager: TransactionManager,
        clock: RunClock,
    ) -> None:
        self._checkpoint_store = checkpoint_store
        self._transaction_manager = transaction_manager
        self._clock = clock
        self._lock = asyncio.Lock()

    async def checkpoint(
        self,
        *,
        run_id: UUID,
        retry_count: int,
        stage: RunStage,
        key: str,
        summary: dict[str, object],
        completed_stages: tuple[str, ...],
        next_stage: str | None,
    ) -> None:
        payload = {
            **summary,
            "attempt": retry_count + 1,
            "completed_stages": list(completed_stages),
            "next_stage": next_stage,
        }
        async with self._lock:
            async with self._transaction_manager.boundary():
                await self._checkpoint_store.append(
                    run_id=run_id,
                    stage=stage,
                    checkpoint_key=f"attempt-{retry_count}:{key}",
                    payload_json=payload,
                    summary_json=summary,
                    created_at=self._clock.now(),
                )
