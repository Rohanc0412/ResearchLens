import asyncio
from collections.abc import Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from researchlens.modules.runs.application.ports import RunEventStore, TransactionManager
from researchlens.modules.runs.application.run_clock import RunClock
from researchlens.modules.runs.domain import (
    RunEventAudience,
    RunEventLevel,
    RunEventType,
    RunStage,
)

RunEventStoreFactory = Callable[[AsyncSession], RunEventStore]
TransactionManagerFactory = Callable[[AsyncSession], TransactionManager]


class RunGraphEventBridge:
    def __init__(
        self,
        *,
        event_store: RunEventStore,
        transaction_manager: TransactionManager,
        clock: RunClock,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        event_store_factory: RunEventStoreFactory | None = None,
        transaction_manager_factory: TransactionManagerFactory | None = None,
    ) -> None:
        self._event_store = event_store
        self._transaction_manager = transaction_manager
        self._clock = clock
        self._lock = asyncio.Lock()
        self._session_factory = session_factory
        self._event_store_factory = event_store_factory
        self._transaction_manager_factory = transaction_manager_factory

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
        async with self._lock:
            if self._uses_isolated_session():
                await self._append_with_isolated_session(
                    run_id=run_id,
                    retry_count=retry_count,
                    cancel_requested=cancel_requested,
                    stage=stage,
                    key=key,
                    level=level,
                    message=message,
                    payload=payload,
                )
                return
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

    def _uses_isolated_session(self) -> bool:
        return (
            self._session_factory is not None
            and self._event_store_factory is not None
            and self._transaction_manager_factory is not None
        )

    async def _append_with_isolated_session(
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
        assert self._session_factory is not None
        assert self._event_store_factory is not None
        assert self._transaction_manager_factory is not None
        async with self._session_factory() as session:
            event_store = self._event_store_factory(session)
            transaction_manager = self._transaction_manager_factory(session)
            async with transaction_manager.boundary():
                await event_store.append(
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
