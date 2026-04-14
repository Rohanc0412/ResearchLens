import asyncio
from collections.abc import Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from researchlens.modules.runs.application.ports import RunCheckpointStore, TransactionManager
from researchlens.modules.runs.application.run_clock import RunClock
from researchlens.modules.runs.domain import RunStage

RunCheckpointStoreFactory = Callable[[AsyncSession], RunCheckpointStore]
TransactionManagerFactory = Callable[[AsyncSession], TransactionManager]


class RunGraphCheckpointBridge:
    def __init__(
        self,
        *,
        checkpoint_store: RunCheckpointStore,
        transaction_manager: TransactionManager,
        clock: RunClock,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        checkpoint_store_factory: RunCheckpointStoreFactory | None = None,
        transaction_manager_factory: TransactionManagerFactory | None = None,
    ) -> None:
        self._checkpoint_store = checkpoint_store
        self._transaction_manager = transaction_manager
        self._clock = clock
        self._lock = asyncio.Lock()
        self._session_factory = session_factory
        self._checkpoint_store_factory = checkpoint_store_factory
        self._transaction_manager_factory = transaction_manager_factory

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
            if self._uses_isolated_session():
                await self._append_with_isolated_session(
                    run_id=run_id,
                    retry_count=retry_count,
                    stage=stage,
                    key=key,
                    payload=payload,
                    summary=summary,
                )
                return
            async with self._transaction_manager.boundary():
                await self._checkpoint_store.append(
                    run_id=run_id,
                    stage=stage,
                    checkpoint_key=f"attempt-{retry_count}:{key}",
                    payload_json=payload,
                    summary_json=summary,
                    created_at=self._clock.now(),
                )

    def _uses_isolated_session(self) -> bool:
        return (
            self._session_factory is not None
            and self._checkpoint_store_factory is not None
            and self._transaction_manager_factory is not None
        )

    async def _append_with_isolated_session(
        self,
        *,
        run_id: UUID,
        retry_count: int,
        stage: RunStage,
        key: str,
        payload: dict[str, object],
        summary: dict[str, object],
    ) -> None:
        assert self._session_factory is not None
        assert self._checkpoint_store_factory is not None
        assert self._transaction_manager_factory is not None
        async with self._session_factory() as session:
            checkpoint_store = self._checkpoint_store_factory(session)
            transaction_manager = self._transaction_manager_factory(session)
            async with transaction_manager.boundary():
                await checkpoint_store.append(
                    run_id=run_id,
                    stage=stage,
                    checkpoint_key=f"attempt-{retry_count}:{key}",
                    payload_json=payload,
                    summary_json=summary,
                    created_at=self._clock.now(),
                )
