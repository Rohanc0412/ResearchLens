from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from researchlens.modules.runs.application import (
    CancelRunUseCase,
    CreateRunUseCase,
    GetRunUseCase,
    ListRunEventsUseCase,
    ProcessRunQueueItemUseCase,
    RetryRunUseCase,
    UtcRunClock,
)
from researchlens.modules.runs.application.ports import RunExecutionOrchestrator
from researchlens.modules.runs.infrastructure.conversation_scope_reader_sql import (
    SqlAlchemyConversationScopeReader,
)
from researchlens.modules.runs.infrastructure.message_scope_reader_sql import (
    SqlAlchemyMessageScopeReader,
)
from researchlens.modules.runs.infrastructure.queue_backend_db import DbRunQueueBackend
from researchlens.modules.runs.infrastructure.run_checkpoint_store_sql import (
    SqlAlchemyRunCheckpointStore,
)
from researchlens.modules.runs.infrastructure.run_event_store_sql import SqlAlchemyRunEventStore
from researchlens.modules.runs.infrastructure.run_repository_sql import SqlAlchemyRunRepository
from researchlens.shared.config import ResearchLensSettings
from researchlens.shared.db import SqlAlchemyTransactionManager


class RunOrchestratorFactory(Protocol):
    def __call__(
        self,
        *,
        session: AsyncSession,
        event_store: SqlAlchemyRunEventStore,
        checkpoint_store: SqlAlchemyRunCheckpointStore,
        transaction_manager: SqlAlchemyTransactionManager,
    ) -> RunExecutionOrchestrator: ...


class _UnavailableRunOrchestrator:
    async def execute(
        self,
        *,
        run: object,
        queue_item_id: object,
        lease_token: object,
    ) -> None:
        raise RuntimeError("Run execution orchestration is not available in this runtime.")


@dataclass(slots=True)
class RunsRequestContext:
    create_run: CreateRunUseCase
    get_run: GetRunUseCase
    list_run_events: ListRunEventsUseCase
    cancel_run: CancelRunUseCase
    retry_run: RetryRunUseCase
    process_run_queue_item: ProcessRunQueueItemUseCase
    queue_backend: DbRunQueueBackend
    transaction_manager: SqlAlchemyTransactionManager


class SqlAlchemyRunsRuntime:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        settings: ResearchLensSettings,
        run_orchestrator_factory: RunOrchestratorFactory | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings
        self._run_orchestrator_factory = run_orchestrator_factory

    @asynccontextmanager
    async def request_context(self) -> AsyncIterator[RunsRequestContext]:
        async with self._session_factory() as session:
            yield self._build_context(session)

    def _build_context(self, session: AsyncSession) -> RunsRequestContext:
        run_repository = SqlAlchemyRunRepository(session)
        event_store = SqlAlchemyRunEventStore(session)
        checkpoint_store = SqlAlchemyRunCheckpointStore(session)
        queue_backend = DbRunQueueBackend(session)
        transaction_manager = SqlAlchemyTransactionManager(session)
        return RunsRequestContext(
            create_run=CreateRunUseCase(
                conversation_scope_reader=SqlAlchemyConversationScopeReader(session),
                message_scope_reader=SqlAlchemyMessageScopeReader(session),
                run_repository=run_repository,
                event_store=event_store,
                queue_backend=queue_backend,
                transaction_manager=transaction_manager,
            ),
            get_run=GetRunUseCase(run_repository),
            list_run_events=ListRunEventsUseCase(
                run_repository=run_repository,
                event_store=event_store,
            ),
            cancel_run=CancelRunUseCase(
                run_repository=run_repository,
                event_store=event_store,
                queue_backend=queue_backend,
                transaction_manager=transaction_manager,
            ),
            retry_run=RetryRunUseCase(
                run_repository=run_repository,
                event_store=event_store,
                checkpoint_store=checkpoint_store,
                queue_backend=queue_backend,
                transaction_manager=transaction_manager,
            ),
            process_run_queue_item=ProcessRunQueueItemUseCase(
                run_repository=run_repository,
                event_store=event_store,
                queue_backend=queue_backend,
                transaction_manager=transaction_manager,
                run_orchestrator=self._build_run_orchestrator(
                    session=session,
                    event_store=event_store,
                    checkpoint_store=checkpoint_store,
                    transaction_manager=transaction_manager,
                ),
                clock=UtcRunClock(),
            ),
            queue_backend=queue_backend,
            transaction_manager=transaction_manager,
        )

    def _build_run_orchestrator(
        self,
        *,
        session: AsyncSession,
        event_store: SqlAlchemyRunEventStore,
        checkpoint_store: SqlAlchemyRunCheckpointStore,
        transaction_manager: SqlAlchemyTransactionManager,
    ) -> RunExecutionOrchestrator:
        if self._run_orchestrator_factory is None:
            return _UnavailableRunOrchestrator()
        return self._run_orchestrator_factory(
            session=session,
            event_store=event_store,
            checkpoint_store=checkpoint_store,
            transaction_manager=transaction_manager,
        )
