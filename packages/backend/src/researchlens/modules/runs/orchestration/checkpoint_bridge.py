import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from researchlens.modules.runs.application.ports import RunCheckpointStore, TransactionManager
from researchlens.modules.runs.application.run_clock import RunClock
from researchlens.modules.runs.domain import RunStage
from researchlens.modules.runs.infrastructure.run_checkpoint_store_sql import (
    SqlAlchemyRunCheckpointStore,
)
from researchlens.shared.db.transaction_manager import SqlAlchemyTransactionManager


class RunGraphCheckpointBridge:
    def __init__(
        self,
        *,
        checkpoint_store: RunCheckpointStore,
        transaction_manager: TransactionManager,
        clock: RunClock,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self._checkpoint_store = checkpoint_store
        self._transaction_manager = transaction_manager
        self._clock = clock
        self._lock = asyncio.Lock()
        self._session_factory = session_factory

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
            if self._session_factory is None:
                async with self._transaction_manager.boundary():
                    await self._checkpoint_store.append(
                        run_id=run_id,
                        stage=stage,
                        checkpoint_key=f"attempt-{retry_count}:{key}",
                        payload_json=payload,
                        summary_json=summary,
                        created_at=self._clock.now(),
                    )
                return

            async with self._session_factory() as session:
                transaction_manager = SqlAlchemyTransactionManager(session)
                checkpoint_store = SqlAlchemyRunCheckpointStore(session)
                async with transaction_manager.boundary():
                    await checkpoint_store.append(
                        run_id=run_id,
                        stage=stage,
                        checkpoint_key=f"attempt-{retry_count}:{key}",
                        payload_json=payload,
                        summary_json=summary,
                        created_at=self._clock.now(),
                    )
