import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

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
)
from researchlens.modules.runs.application.dto import RunEventView, RunSummaryView
from researchlens.modules.runs.domain import RunStage, RunStatus
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


class ControlledStageExecution:
    def __init__(
        self,
        *,
        fail_before_stage: RunStage | None = None,
        crash_after_stage: RunStage | None = None,
        wait_stage: RunStage | None = None,
        wait_ready: asyncio.Event | None = None,
        wait_release: asyncio.Event | None = None,
    ) -> None:
        self._fail_before_stage = fail_before_stage
        self._crash_after_stage = crash_after_stage
        self._wait_stage = wait_stage
        self._wait_ready = wait_ready
        self._wait_release = wait_release

    async def before_stage(self, *, run: object, stage: RunStage) -> None:
        if stage == self._fail_before_stage:
            raise RuntimeError(f"planned failure at {stage.value}")
        if (
            stage == self._wait_stage
            and self._wait_ready is not None
            and self._wait_release is not None
        ):
            self._wait_ready.set()
            await self._wait_release.wait()

    async def after_stage(self, *, run: object, stage: RunStage) -> None:
        if stage == self._crash_after_stage:
            raise WorkerCrash(f"worker crashed after {stage.value}")


@pytest.mark.asyncio
async def test_queue_lease_is_exclusive_and_expired_lease_can_be_reclaimed(
    database_runtime: DatabaseRuntime,
) -> None:
    tenant_id, user_id, conversation_id = await _seed_project_conversation(database_runtime)
    run_id = await _create_run(
        database_runtime,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    claimed_one = await _claim_one(database_runtime, now=datetime.now(tz=UTC))
    claimed_two = await _claim_one(database_runtime, now=datetime.now(tz=UTC))
    reclaimed = await _claim_one(database_runtime, now=datetime.now(tz=UTC) + timedelta(seconds=31))

    assert claimed_one is not None
    assert claimed_one.run_id == run_id
    assert claimed_two is None
    assert reclaimed is not None
    assert reclaimed.run_id == run_id


@pytest.mark.asyncio
async def test_retry_before_drafting_uses_latest_successful_checkpoint(
    database_runtime: DatabaseRuntime,
) -> None:
    tenant_id, user_id, conversation_id = await _seed_project_conversation(database_runtime)
    run_id = await _create_run(
        database_runtime,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    claimed = await _claim_one(database_runtime, now=datetime.now(tz=UTC))
    assert claimed is not None

    await _process_claimed(
        database_runtime,
        claimed=claimed,
        stage_execution=ControlledStageExecution(fail_before_stage=RunStage.DRAFT),
    )
    retried = await _retry_run(database_runtime, tenant_id=tenant_id, run_id=run_id)

    assert retried.status == "queued"
    assert retried.current_stage == "retrieve"
    assert retried.retry_count == 1


@pytest.mark.asyncio
async def test_retry_after_drafting_restarts_from_draft(
    database_runtime: DatabaseRuntime,
) -> None:
    tenant_id, user_id, conversation_id = await _seed_project_conversation(database_runtime)
    run_id = await _create_run(
        database_runtime,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    claimed = await _claim_one(database_runtime, now=datetime.now(tz=UTC))
    assert claimed is not None

    await _process_claimed(
        database_runtime,
        claimed=claimed,
        stage_execution=ControlledStageExecution(fail_before_stage=RunStage.EVALUATE),
    )
    retried = await _retry_run(database_runtime, tenant_id=tenant_id, run_id=run_id)

    assert retried.status == "queued"
    assert retried.current_stage == "draft"
    assert retried.retry_count == 1


@pytest.mark.asyncio
async def test_worker_restart_resumes_from_checkpoint_without_duplicate_stage_completion(
    database_runtime: DatabaseRuntime,
) -> None:
    tenant_id, user_id, conversation_id = await _seed_project_conversation(database_runtime)
    run_id = await _create_run(
        database_runtime,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    claimed = await _claim_one(database_runtime, now=datetime.now(tz=UTC))
    assert claimed is not None

    with pytest.raises(WorkerCrash):
        await _process_claimed(
            database_runtime,
            claimed=claimed,
            stage_execution=ControlledStageExecution(crash_after_stage=RunStage.RETRIEVE),
        )

    reclaimed = await _claim_one(database_runtime, now=datetime.now(tz=UTC) + timedelta(seconds=31))
    assert reclaimed is not None
    await _process_claimed(
        database_runtime,
        claimed=reclaimed,
        stage_execution=ControlledStageExecution(),
    )
    events = await _list_run_events(database_runtime, tenant_id=tenant_id, run_id=run_id)
    run = await _get_run(database_runtime, tenant_id=tenant_id, run_id=run_id)

    retrieve_completions = [
        event
        for event in events
        if event.event_type == "stage.completed" and event.stage == "retrieve"
    ]
    assert len(retrieve_completions) == 1
    assert run.status == "succeeded"


@pytest.mark.asyncio
async def test_running_cancel_requests_stop_and_worker_finishes_cleanly(
    database_runtime: DatabaseRuntime,
) -> None:
    tenant_id, user_id, conversation_id = await _seed_project_conversation(database_runtime)
    run_id = await _create_run(
        database_runtime,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    claimed = await _claim_one(database_runtime, now=datetime.now(tz=UTC))
    assert claimed is not None

    await _mark_run_running(database_runtime, run_id=run_id)
    await _cancel_run(database_runtime, tenant_id=tenant_id, run_id=run_id)
    await _process_claimed(
        database_runtime,
        claimed=claimed,
        stage_execution=ControlledStageExecution(),
    )
    run = await _get_run(database_runtime, tenant_id=tenant_id, run_id=run_id)
    events = await _list_run_events(database_runtime, tenant_id=tenant_id, run_id=run_id)

    assert run.status == "canceled"
    assert any(event.event_type == "cancel.requested" for event in events)
    assert any(event.event_type == "run.canceled" for event in events)


async def _seed_project_conversation(
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


async def _create_run(
    database_runtime: DatabaseRuntime,
    *,
    tenant_id: UUID,
    user_id: UUID,
    conversation_id: UUID,
) -> UUID:
    async with database_runtime.session_factory() as session:
        use_case = CreateRunUseCase(
            conversation_scope_reader=SqlAlchemyConversationScopeReader(session),
            message_scope_reader=SqlAlchemyMessageScopeReader(session),
            run_repository=SqlAlchemyRunRepository(session),
            event_store=SqlAlchemyRunEventStore(session),
            queue_backend=DbRunQueueBackend(session),
            transaction_manager=SqlAlchemyTransactionManager(session),
        )
        result = await use_case.execute(
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


async def _claim_one(
    database_runtime: DatabaseRuntime,
    *,
    now: datetime,
) -> RunQueueItem | None:
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


async def _process_claimed(
    database_runtime: DatabaseRuntime,
    *,
    claimed: RunQueueItem,
    stage_execution: ControlledStageExecution,
) -> None:
    async with database_runtime.session_factory() as session:
        use_case = ProcessRunQueueItemUseCase(
            run_repository=SqlAlchemyRunRepository(session),
            event_store=SqlAlchemyRunEventStore(session),
            checkpoint_store=SqlAlchemyRunCheckpointStore(session),
            queue_backend=DbRunQueueBackend(session),
            transaction_manager=SqlAlchemyTransactionManager(session),
            stage_controller=stage_execution,
            queue_lease_seconds=30,
        )
        await use_case.execute(
            ProcessRunQueueItemCommand(
                queue_item_id=claimed.id,
                lease_token=claimed.lease_token or uuid4(),
                run_id=claimed.run_id,
            )
        )


async def _retry_run(
    database_runtime: DatabaseRuntime,
    *,
    tenant_id: UUID,
    run_id: UUID,
) -> RunSummaryView:
    async with database_runtime.session_factory() as session:
        use_case = RetryRunUseCase(
            run_repository=SqlAlchemyRunRepository(session),
            event_store=SqlAlchemyRunEventStore(session),
            checkpoint_store=SqlAlchemyRunCheckpointStore(session),
            queue_backend=DbRunQueueBackend(session),
            transaction_manager=SqlAlchemyTransactionManager(session),
        )
        return await use_case.execute(RetryRunCommand(tenant_id=tenant_id, run_id=run_id))


async def _cancel_run(
    database_runtime: DatabaseRuntime,
    *,
    tenant_id: UUID,
    run_id: UUID,
) -> RunSummaryView:
    async with database_runtime.session_factory() as session:
        use_case = CancelRunUseCase(
            run_repository=SqlAlchemyRunRepository(session),
            event_store=SqlAlchemyRunEventStore(session),
            queue_backend=DbRunQueueBackend(session),
            transaction_manager=SqlAlchemyTransactionManager(session),
        )
        return await use_case.execute(CancelRunCommand(tenant_id=tenant_id, run_id=run_id))


async def _mark_run_running(database_runtime: DatabaseRuntime, *, run_id: UUID) -> None:
    now = datetime.now(tz=UTC)
    async with database_runtime.session_factory() as session:
        repository = SqlAlchemyRunRepository(session)
        transaction_manager = SqlAlchemyTransactionManager(session)
        async with transaction_manager.boundary():
            run = await repository.get_by_id_for_update(run_id=run_id)
            assert run is not None
            updated_run = run.replace_values(
                status=RunStatus.RUNNING,
                started_at=now,
                updated_at=now,
            )
            await repository.save(updated_run)


async def _get_run(
    database_runtime: DatabaseRuntime,
    *,
    tenant_id: UUID,
    run_id: UUID,
) -> RunSummaryView:
    async with database_runtime.session_factory() as session:
        use_case = GetRunUseCase(SqlAlchemyRunRepository(session))
        return await use_case.execute(GetRunQuery(tenant_id=tenant_id, run_id=run_id))


async def _list_run_events(
    database_runtime: DatabaseRuntime,
    *,
    tenant_id: UUID,
    run_id: UUID,
) -> list[RunEventView]:
    async with database_runtime.session_factory() as session:
        use_case = ListRunEventsUseCase(
            run_repository=SqlAlchemyRunRepository(session),
            event_store=SqlAlchemyRunEventStore(session),
        )
        return await use_case.execute(ListRunEventsQuery(tenant_id=tenant_id, run_id=run_id))
