from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from researchlens.modules.conversations.infrastructure.rows.conversation_row import ConversationRow
from researchlens.modules.projects.infrastructure.project_row import ProjectRow
from researchlens.modules.runs.application import CreateRunCommand, CreateRunUseCase
from researchlens.modules.runs.application.dto import RunEventView
from researchlens.modules.runs.domain import RunEventAudience, RunEventLevel, RunEventType, RunStage
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
from researchlens.modules.runs.presentation.run_sse import (
    RunStreamContextFactory,
    stream_run_events,
)
from researchlens.shared.db import DatabaseRuntime, SqlAlchemyTransactionManager


class FakeListRunEventsUseCase:
    def __init__(self, events: list[RunEventView]) -> None:
        self._events = events

    async def execute(self, query: Any) -> list[RunEventView]:
        if query.after_event_number is None:
            return self._events
        return [event for event in self._events if event.event_number > query.after_event_number]


class FakeGetRunUseCase:
    def __init__(self, statuses: list[str]) -> None:
        self._statuses = statuses
        self._index = 0

    async def execute(self, query: Any) -> Any:
        status = self._statuses[min(self._index, len(self._statuses) - 1)]
        self._index += 1
        return type("RunSummary", (), {"status": status})()


class FakeRunStreamContext:
    def __init__(self, events: list[RunEventView], statuses: list[str]) -> None:
        self.list_run_events = FakeListRunEventsUseCase(events)
        self.get_run = FakeGetRunUseCase(statuses)


def fake_request_context_factory(
    events: list[RunEventView],
    statuses: list[str],
) -> RunStreamContextFactory:
    @asynccontextmanager
    async def _factory() -> AsyncIterator[FakeRunStreamContext]:
        yield FakeRunStreamContext(events, statuses)

    return cast(RunStreamContextFactory, _factory)


@pytest.mark.asyncio
async def test_duplicate_event_append_returns_existing_row(
    database_runtime: DatabaseRuntime,
) -> None:
    run_id = await _seed_run(database_runtime)
    async with database_runtime.session_factory() as session:
        event_store = SqlAlchemyRunEventStore(session)
        transaction_manager = SqlAlchemyTransactionManager(session)
        async with transaction_manager.boundary():
            first = await event_store.append(
                run_id=run_id,
                event_type=RunEventType.RUN_QUEUED,
                audience=RunEventAudience.STATE,
                level=RunEventLevel.INFO,
                status="queued",
                stage="retrieve",
                message="Waiting for an available worker",
                payload_json=None,
                retry_count=0,
                cancel_requested=False,
                created_at=datetime.now(tz=UTC),
                event_key="same-event",
            )
            second = await event_store.append(
                run_id=run_id,
                event_type=RunEventType.RUN_QUEUED,
                audience=RunEventAudience.STATE,
                level=RunEventLevel.INFO,
                status="queued",
                stage="retrieve",
                message="Waiting for an available worker",
                payload_json=None,
                retry_count=0,
                cancel_requested=False,
                created_at=datetime.now(tz=UTC),
                event_key="same-event",
            )
        events = await event_store.list_for_run(run_id=run_id, after_event_number=None)

    assert first.id == second.id
    assert len(events) == 3


@pytest.mark.asyncio
async def test_duplicate_checkpoint_append_returns_existing_row(
    database_runtime: DatabaseRuntime,
) -> None:
    run_id = await _seed_run(database_runtime)
    async with database_runtime.session_factory() as session:
        checkpoint_store = SqlAlchemyRunCheckpointStore(session)
        transaction_manager = SqlAlchemyTransactionManager(session)
        async with transaction_manager.boundary():
            first = await checkpoint_store.append(
                run_id=run_id,
                stage=RunStage.RETRIEVE,
                checkpoint_key="retrieve:v1",
                payload_json={"next_stage": "draft"},
                summary_json={"current_stage": "retrieve"},
                created_at=datetime.now(tz=UTC),
            )
            second = await checkpoint_store.append(
                run_id=run_id,
                stage=RunStage.RETRIEVE,
                checkpoint_key="retrieve:v1",
                payload_json={"next_stage": "draft"},
                summary_json={"current_stage": "retrieve"},
                created_at=datetime.now(tz=UTC),
            )
        checkpoints = await checkpoint_store.list_for_run(run_id=run_id)

    assert first.id == second.id
    assert len(checkpoints) == 1


@pytest.mark.asyncio
async def test_queue_claim_respects_max_attempts(database_runtime: DatabaseRuntime) -> None:
    run_id = await _seed_run(database_runtime)
    async with database_runtime.session_factory() as session:
        queue_backend = DbRunQueueBackend(session)
        transaction_manager = SqlAlchemyTransactionManager(session)
        async with transaction_manager.boundary():
            await queue_backend.enqueue(
                tenant_id=uuid4(),
                run_id=run_id,
                available_at=datetime.now(tz=UTC),
            )
        async with transaction_manager.boundary():
            first = await queue_backend.claim_available(
                now=datetime.now(tz=UTC),
                lease_duration=timedelta(seconds=30),
                limit=1,
                max_attempts=1,
            )
            if first:
                await queue_backend.release(
                    queue_item_id=first[0].id,
                    lease_token=first[0].lease_token or uuid4(),
                    available_at=datetime.now(tz=UTC),
                    last_error="planned",
                )
        async with transaction_manager.boundary():
            second = await queue_backend.claim_available(
                now=datetime.now(tz=UTC) + timedelta(seconds=31),
                lease_duration=timedelta(seconds=30),
                limit=1,
                max_attempts=1,
            )

    assert len(first) == 1
    assert second == []


@pytest.mark.asyncio
async def test_terminal_stream_closes_after_grace_window() -> None:
    event = RunEventView(
        run_id=uuid4(),
        event_number=1,
        event_type="run.succeeded",
        status="succeeded",
        stage="export",
        display_status="Completed",
        display_stage="Exporting result",
        message="Run completed successfully",
        retry_count=0,
        cancel_requested=False,
        payload=None,
        ts=datetime.now(tz=UTC),
    )
    stream = stream_run_events(
        tenant_id=uuid4(),
        run_id=uuid4(),
        last_event_id=None,
        request_context_factory=fake_request_context_factory([event], ["succeeded", "succeeded"]),
        keepalive_seconds=0,
        terminal_grace_seconds=0,
    )

    items = []
    async for chunk in stream:
        items.append(chunk)

    assert any("event: run.succeeded" in item for item in items)
    assert any(": keepalive" in item for item in items)
    assert len(items) < 10


async def _seed_run(database_runtime: DatabaseRuntime) -> UUID:
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
