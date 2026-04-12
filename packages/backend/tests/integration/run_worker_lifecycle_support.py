import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from researchlens.modules.conversations.infrastructure.rows.conversation_row import ConversationRow
from researchlens.modules.projects.infrastructure.project_row import ProjectRow
from researchlens.modules.runs.application import (
    CancelRunCommand,
    CancelRunUseCase,
    CreateRunCommand,
    CreateRunUseCase,
    GetRunQuery,
    GetRunUseCase,
    ListRunEventsQuery,
    ListRunEventsUseCase,
    ProcessRunQueueItemCommand,
    ProcessRunQueueItemUseCase,
    RetryRunCommand,
    RetryRunUseCase,
    UtcRunClock,
)
from researchlens.modules.runs.application.dto import ResumeState, RunEventView, RunSummaryView
from researchlens.modules.runs.application.run_execution_support import RunExecutionMutations
from researchlens.modules.runs.application.run_terminal_mutations import RunTerminalMutations
from researchlens.modules.runs.domain import Run, RunStage, RunStatus
from researchlens.modules.runs.domain.run_record import RunQueueItem
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
from researchlens.shared.db import DatabaseRuntime, SqlAlchemyTransactionManager


class WorkerCrash(BaseException):
    pass


class ControlledRunExecutionOrchestrator:
    def __init__(
        self,
        *,
        fail_before_stage: RunStage | None = None,
        fail_after_stage: RunStage | None = None,
        crash_after_stage: RunStage | None = None,
        wait_stage: RunStage | None = None,
        wait_ready: asyncio.Event | None = None,
        wait_release: asyncio.Event | None = None,
    ) -> None:
        self._fail_before_stage = fail_before_stage
        self._fail_after_stage = fail_after_stage
        self._crash_after_stage = crash_after_stage
        self._wait_stage = wait_stage
        self._wait_ready = wait_ready
        self._wait_release = wait_release

    def bind(
        self,
        *,
        repository: SqlAlchemyRunRepository,
        event_store: SqlAlchemyRunEventStore,
        checkpoint_store: SqlAlchemyRunCheckpointStore,
        queue_backend: DbRunQueueBackend,
        transaction_manager: SqlAlchemyTransactionManager,
    ) -> "_BoundControlledRunExecutionOrchestrator":
        return _BoundControlledRunExecutionOrchestrator(
            config=self,
            repository=repository,
            event_store=event_store,
            checkpoint_store=checkpoint_store,
            queue_backend=queue_backend,
            transaction_manager=transaction_manager,
        )


class _BoundControlledRunExecutionOrchestrator:
    def __init__(
        self,
        *,
        config: ControlledRunExecutionOrchestrator,
        repository: SqlAlchemyRunRepository,
        event_store: SqlAlchemyRunEventStore,
        checkpoint_store: SqlAlchemyRunCheckpointStore,
        queue_backend: DbRunQueueBackend,
        transaction_manager: SqlAlchemyTransactionManager,
    ) -> None:
        self._config = config
        self._repository = repository
        self._queue_backend = queue_backend
        self._clock = UtcRunClock()
        self._mutations = RunExecutionMutations(
            run_repository=repository,
            event_store=event_store,
            checkpoint_store=checkpoint_store,
            transaction_manager=transaction_manager,
            clock=self._clock,
        )
        self._terminal_mutations = RunTerminalMutations(
            run_repository=repository,
            event_store=event_store,
            transaction_manager=transaction_manager,
            clock=self._clock,
        )

    async def execute(
        self,
        *,
        run: Run,
        queue_item_id: UUID,
        lease_token: UUID,
    ) -> None:
        current_run = run
        resume_state = await self._mutations.load_resume_state(current_run)
        if current_run.status == RunStatus.QUEUED:
            current_run = await self._mutations.start_run(
                run=current_run,
                stage=resume_state.start_stage,
            )
        for stage in (RunStage.RETRIEVE, RunStage.DRAFT):
            if stage.value in {item.value for item in resume_state.completed_stages}:
                continue
            if stage != resume_state.start_stage and stage == RunStage.RETRIEVE:
                continue
            current_run = (
                await self._repository.get_by_id_for_update(run_id=current_run.id) or current_run
            )
            if current_run.cancel_requested_at is not None:
                await self._terminal_mutations.finalize_cancel(run=current_run)
                return
            await self._mutations.append_stage_started(run=current_run, stage=stage)
            await self._queue_backend.heartbeat(
                queue_item_id=queue_item_id,
                lease_token=lease_token,
                lease_expires_at=self._clock.now() + timedelta(seconds=30),
            )
            await self._before_stage(stage=stage)
            current_run = (
                await self._repository.get_by_id_for_update(run_id=current_run.id) or current_run
            )
            current_run = await self._mutations.complete_stage(
                run=current_run,
                stage=stage,
                resume_state=ResumeState(
                    start_stage=resume_state.start_stage,
                    completed_stages=resume_state.completed_stages,
                    latest_checkpoint=resume_state.latest_checkpoint,
                ),
            )
            await self._after_stage(stage=stage)
        current_run = (
            await self._repository.get_by_id_for_update(run_id=current_run.id) or current_run
        )
        if current_run.cancel_requested_at is not None:
            await self._terminal_mutations.finalize_cancel(run=current_run)
        else:
            await self._terminal_mutations.finalize_success(run=current_run)

    async def _before_stage(self, *, stage: RunStage) -> None:
        if stage == self._config._fail_before_stage:
            raise RuntimeError(f"planned failure at {stage.value}")
        if (
            stage == self._config._wait_stage
            and self._config._wait_ready
            and self._config._wait_release
        ):
            self._config._wait_ready.set()
            await self._config._wait_release.wait()

    async def _after_stage(self, *, stage: RunStage) -> None:
        if stage == self._config._fail_after_stage:
            raise RuntimeError(f"planned failure after {stage.value}")
        if stage == self._config._crash_after_stage:
            raise WorkerCrash(f"worker crashed after {stage.value}")


async def seed_project_conversation(
    database_runtime: DatabaseRuntime,
) -> tuple[UUID, UUID, UUID]:
    tenant_id = uuid4()
    user_id = uuid4()
    project_id = uuid4()
    conversation_id = uuid4()
    now = datetime.now(tz=UTC)
    async with database_runtime.session_factory() as session:
        session.add(
            ProjectRow(
                id=project_id,
                tenant_id=tenant_id,
                name="Alpha",
                description=None,
                created_by=str(user_id),
                created_at=now,
                updated_at=now,
            )
        )
        session.add(
            ConversationRow(
                id=conversation_id,
                tenant_id=tenant_id,
                project_id=project_id,
                created_by_user_id=user_id,
                title="Thread",
                created_at=now,
                updated_at=now,
                last_message_at=None,
            )
        )
        await session.commit()
    return tenant_id, user_id, conversation_id


async def create_run(
    database_runtime: DatabaseRuntime,
    *,
    tenant_id: UUID,
    user_id: UUID,
    conversation_id: UUID,
) -> UUID:
    async with database_runtime.session_factory() as session:
        result = await CreateRunUseCase(
            conversation_scope_reader=SqlAlchemyConversationScopeReader(session),
            message_scope_reader=SqlAlchemyMessageScopeReader(session),
            run_repository=SqlAlchemyRunRepository(session),
            event_store=SqlAlchemyRunEventStore(session),
            queue_backend=DbRunQueueBackend(session),
            transaction_manager=SqlAlchemyTransactionManager(session),
        ).execute(
            CreateRunCommand(
                tenant_id=tenant_id,
                user_id=user_id,
                conversation_id=conversation_id,
                source_message_id=None,
                request_text="Start a run",
                client_request_id=None,
                output_type="report",
            )
        )
        return result.run.id


async def claim_one(database_runtime: DatabaseRuntime, *, now: datetime) -> RunQueueItem | None:
    async with database_runtime.session_factory() as session:
        queue_backend = DbRunQueueBackend(session)
        transaction_manager = SqlAlchemyTransactionManager(session)
        async with transaction_manager.boundary():
            claimed = await queue_backend.claim_available(
                now=now,
                lease_duration=timedelta(seconds=30),
                limit=1,
                max_attempts=5,
            )
        return claimed[0] if claimed else None


async def process_claimed(
    database_runtime: DatabaseRuntime,
    *,
    claimed: RunQueueItem,
    stage_execution: ControlledRunExecutionOrchestrator,
) -> None:
    async with database_runtime.session_factory() as session:
        repository = SqlAlchemyRunRepository(session)
        event_store = SqlAlchemyRunEventStore(session)
        checkpoint_store = SqlAlchemyRunCheckpointStore(session)
        queue_backend = DbRunQueueBackend(session)
        transaction_manager = SqlAlchemyTransactionManager(session)
        await ProcessRunQueueItemUseCase(
            run_repository=repository,
            event_store=event_store,
            queue_backend=queue_backend,
            transaction_manager=transaction_manager,
            run_orchestrator=stage_execution.bind(
                repository=repository,
                event_store=event_store,
                checkpoint_store=checkpoint_store,
                queue_backend=queue_backend,
                transaction_manager=transaction_manager,
            ),
        ).execute(
            ProcessRunQueueItemCommand(
                queue_item_id=claimed.id,
                lease_token=claimed.lease_token or uuid4(),
                run_id=claimed.run_id,
            )
        )


async def retry_run(
    database_runtime: DatabaseRuntime,
    *,
    tenant_id: UUID,
    run_id: UUID,
) -> RunSummaryView:
    async with database_runtime.session_factory() as session:
        return await RetryRunUseCase(
            run_repository=SqlAlchemyRunRepository(session),
            event_store=SqlAlchemyRunEventStore(session),
            checkpoint_store=SqlAlchemyRunCheckpointStore(session),
            queue_backend=DbRunQueueBackend(session),
            transaction_manager=SqlAlchemyTransactionManager(session),
        ).execute(RetryRunCommand(tenant_id=tenant_id, run_id=run_id))


async def cancel_run(
    database_runtime: DatabaseRuntime,
    *,
    tenant_id: UUID,
    run_id: UUID,
) -> RunSummaryView:
    async with database_runtime.session_factory() as session:
        return await CancelRunUseCase(
            run_repository=SqlAlchemyRunRepository(session),
            event_store=SqlAlchemyRunEventStore(session),
            queue_backend=DbRunQueueBackend(session),
            transaction_manager=SqlAlchemyTransactionManager(session),
        ).execute(CancelRunCommand(tenant_id=tenant_id, run_id=run_id))


async def mark_run_running(database_runtime: DatabaseRuntime, *, run_id: UUID) -> None:
    now = datetime.now(tz=UTC)
    async with database_runtime.session_factory() as session:
        repository = SqlAlchemyRunRepository(session)
        transaction_manager = SqlAlchemyTransactionManager(session)
        async with transaction_manager.boundary():
            run = await repository.get_by_id_for_update(run_id=run_id)
            assert run is not None
            await repository.save(
                run.replace_values(
                    status=RunStatus.RUNNING,
                    started_at=now,
                    updated_at=now,
                )
            )


async def get_run(
    database_runtime: DatabaseRuntime,
    *,
    tenant_id: UUID,
    run_id: UUID,
) -> RunSummaryView:
    async with database_runtime.session_factory() as session:
        return await GetRunUseCase(SqlAlchemyRunRepository(session)).execute(
            GetRunQuery(tenant_id=tenant_id, run_id=run_id)
        )


async def list_run_events(
    database_runtime: DatabaseRuntime,
    *,
    tenant_id: UUID,
    run_id: UUID,
) -> list[RunEventView]:
    async with database_runtime.session_factory() as session:
        return await ListRunEventsUseCase(
            run_repository=SqlAlchemyRunRepository(session),
            event_store=SqlAlchemyRunEventStore(session),
        ).execute(ListRunEventsQuery(tenant_id=tenant_id, run_id=run_id))
