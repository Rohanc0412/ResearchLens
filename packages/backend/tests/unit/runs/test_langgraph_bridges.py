import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest

from researchlens.modules.runs.application.run_clock import UtcRunClock
from researchlens.modules.runs.domain import (
    Run,
    RunCheckpointRecord,
    RunEventRecord,
    RunStage,
    RunStatus,
)
from researchlens.modules.runs.orchestration.checkpoint_bridge import RunGraphCheckpointBridge
from researchlens.modules.runs.orchestration.event_bridge import RunGraphEventBridge
from researchlens.modules.runs.orchestration.runtime_bridge import RunGraphRuntimeBridge
from researchlens.modules.runs.orchestration.state import RunGraphState, restore_graph_state


class _NoopTransactionManager:
    @asynccontextmanager
    async def boundary(self) -> AsyncIterator[None]:
        yield

    async def rollback(self) -> None:
        return None


@dataclass
class _CapturedEvent:
    event_key: str | None
    stage: str | None
    message: str


class _FakeEventStore:
    def __init__(self) -> None:
        self.captured: list[_CapturedEvent] = []

    async def append(self, **kwargs):  # type: ignore[no-untyped-def]
        self.captured.append(
            _CapturedEvent(
                event_key=kwargs["event_key"],
                stage=kwargs["stage"],
                message=kwargs["message"],
            )
        )
        return RunEventRecord(
            id=uuid4(),
            run_id=kwargs["run_id"],
            event_number=1,
            event_type=kwargs["event_type"],
            audience=kwargs["audience"],
            level=kwargs["level"],
            status=RunStatus(kwargs["status"]),
            stage=RunStage(kwargs["stage"]) if kwargs["stage"] else None,
            message=kwargs["message"],
            payload_json=kwargs["payload_json"],
            retry_count=kwargs["retry_count"],
            cancel_requested=kwargs["cancel_requested"],
            created_at=kwargs["created_at"],
            event_key=kwargs["event_key"],
        )

    async def list_for_run(self, *, run_id, after_event_number):  # type: ignore[no-untyped-def]
        return []


@dataclass
class _CapturedCheckpoint:
    checkpoint_key: str
    payload_json: dict[str, object] | None


class _FakeCheckpointStore:
    def __init__(self) -> None:
        self.captured: list[_CapturedCheckpoint] = []

    async def append(self, **kwargs):  # type: ignore[no-untyped-def]
        self.captured.append(
            _CapturedCheckpoint(
                checkpoint_key=kwargs["checkpoint_key"],
                payload_json=kwargs["payload_json"],
            )
        )
        return RunCheckpointRecord(
            id=uuid4(),
            run_id=kwargs["run_id"],
            stage=kwargs["stage"],
            checkpoint_key=kwargs["checkpoint_key"],
            payload_json=kwargs["payload_json"],
            summary_json=kwargs["summary_json"],
            created_at=kwargs["created_at"],
        )

    async def latest_for_run(self, *, run_id):  # type: ignore[no-untyped-def]
        return None

    async def list_for_run(self, *, run_id):  # type: ignore[no-untyped-def]
        return []


class _FakeRunRepository:
    def __init__(self, run: Run) -> None:
        self._run = run

    async def get_by_id(self, *, run_id):  # type: ignore[no-untyped-def]
        return self._run

    async def get_by_id_for_update(self, *, run_id):  # type: ignore[no-untyped-def]
        return self._run

    async def save(self, run: Run) -> Run:
        self._run = run
        return run

    async def add(self, run: Run) -> Run:
        raise NotImplementedError

    async def get_by_id_for_tenant(self, *, tenant_id, run_id):  # type: ignore[no-untyped-def]
        return self._run

    async def get_by_client_request_id(self, **kwargs):  # type: ignore[no-untyped-def]
        return None

    async def add_transition(self, transition):  # type: ignore[no-untyped-def]
        return transition


class _FakeQueueBackend:
    async def heartbeat(self, **kwargs):  # type: ignore[no-untyped-def]
        return True

    async def enqueue(self, **kwargs: Any) -> Any:
        raise NotImplementedError

    async def claim_available(self, **kwargs: Any) -> Any:
        raise NotImplementedError

    async def complete(self, **kwargs: Any) -> bool:
        raise NotImplementedError

    async def release(self, **kwargs: Any) -> bool:
        raise NotImplementedError

    async def cancel_active_for_run(self, **kwargs: Any) -> None:
        raise NotImplementedError


class _ConcurrentEventStore:
    def __init__(self) -> None:
        self.active_calls = 0
        self.max_active_calls = 0

    async def append(self, **kwargs):  # type: ignore[no-untyped-def]
        self.active_calls += 1
        self.max_active_calls = max(self.max_active_calls, self.active_calls)
        await asyncio.sleep(0)
        self.active_calls -= 1
        return RunEventRecord(
            id=uuid4(),
            run_id=kwargs["run_id"],
            event_number=1,
            event_type=kwargs["event_type"],
            audience=kwargs["audience"],
            level=kwargs["level"],
            status=RunStatus(kwargs["status"]),
            stage=RunStage(kwargs["stage"]) if kwargs["stage"] else None,
            message=kwargs["message"],
            payload_json=kwargs["payload_json"],
            retry_count=kwargs["retry_count"],
            cancel_requested=kwargs["cancel_requested"],
            created_at=kwargs["created_at"],
            event_key=kwargs["event_key"],
        )


class _ConcurrentCheckpointStore:
    def __init__(self) -> None:
        self.active_calls = 0
        self.max_active_calls = 0

    async def append(self, **kwargs):  # type: ignore[no-untyped-def]
        self.active_calls += 1
        self.max_active_calls = max(self.max_active_calls, self.active_calls)
        await asyncio.sleep(0)
        self.active_calls -= 1
        return RunCheckpointRecord(
            id=uuid4(),
            run_id=kwargs["run_id"],
            stage=kwargs["stage"],
            checkpoint_key=kwargs["checkpoint_key"],
            payload_json=kwargs["payload_json"],
            summary_json=kwargs["summary_json"],
            created_at=kwargs["created_at"],
        )


class _FailIfUsedTransactionManager:
    @asynccontextmanager
    async def boundary(self) -> AsyncIterator[None]:
        raise AssertionError("shared transaction manager should not be used")
        yield


class _FakeIsolatedTransactionManager:
    def __init__(self, session: object) -> None:
        self.session = session

    @asynccontextmanager
    async def boundary(self) -> AsyncIterator[None]:
        yield


class _FakeIsolatedEventStore:
    created_sessions: list[object] = []
    appended_messages: list[str] = []

    def __init__(self, session: object) -> None:
        self.created_sessions.append(session)

    async def append(self, **kwargs: Any) -> RunEventRecord:
        self.appended_messages.append(kwargs["message"])
        return cast(
            RunEventRecord,
            await _FakeEventStore().append(**kwargs),  # type: ignore[no-untyped-call]
        )


class _FakeIsolatedCheckpointStore:
    created_sessions: list[object] = []
    appended_keys: list[str] = []

    def __init__(self, session: object) -> None:
        self.created_sessions.append(session)

    async def append(self, **kwargs: Any) -> RunCheckpointRecord:
        self.appended_keys.append(kwargs["checkpoint_key"])
        return cast(
            RunCheckpointRecord,
            await _FakeCheckpointStore().append(**kwargs),  # type: ignore[no-untyped-call]
        )


class _FakeSessionFactory:
    def __init__(self, session: object) -> None:
        self.session = session
        self.calls = 0

    @asynccontextmanager
    async def __call__(self) -> AsyncIterator[object]:
        self.calls += 1
        yield self.session


def _run(cancel_requested: bool = False) -> Run:
    now = datetime.now(tz=UTC)
    return Run.create(
        id=uuid4(),
        tenant_id=uuid4(),
        project_id=uuid4(),
        conversation_id=uuid4(),
        created_by_user_id=uuid4(),
        output_type="report",
        trigger_message_id=None,
        client_request_id=None,
        created_at=now,
        updated_at=now,
    ).replace_values(
        status=RunStatus.RUNNING,
        cancel_requested_at=now if cancel_requested else None,
        started_at=now,
        updated_at=now,
    )


def test_restore_graph_state_uses_checkpoint_next_stage() -> None:
    run = _run()
    checkpoint = RunCheckpointRecord(
        id=uuid4(),
        run_id=run.id,
        stage=RunStage.RETRIEVE,
        checkpoint_key="attempt-0:retrieval:summary",
        payload_json={"completed_stages": [], "next_stage": "draft"},
        summary_json={"selected_sources": 3},
        created_at=datetime.now(tz=UTC),
    )

    state = restore_graph_state(
        run=run,
        request_text="Question",
        latest_checkpoint=checkpoint,
    )

    assert state["start_stage"] == "draft"
    assert state["resuming"] is True


@pytest.mark.asyncio
async def test_event_bridge_prefixes_event_keys_by_attempt() -> None:
    event_store = _FakeEventStore()
    bridge = RunGraphEventBridge(
        event_store=event_store,
        transaction_manager=_NoopTransactionManager(),
        clock=UtcRunClock(),
    )

    await bridge.info(
        run_id=uuid4(),
        retry_count=2,
        cancel_requested=False,
        stage=RunStage.RETRIEVE,
        key="retrieval:outline-started",
        message="Outline started",
        payload={},
    )

    assert event_store.captured[0].event_key == "attempt-2:retrieval:outline-started"


@pytest.mark.asyncio
async def test_checkpoint_bridge_preserves_lifecycle_resume_fields() -> None:
    checkpoint_store = _FakeCheckpointStore()
    bridge = RunGraphCheckpointBridge(
        checkpoint_store=checkpoint_store,
        transaction_manager=_NoopTransactionManager(),
        clock=UtcRunClock(),
    )

    await bridge.checkpoint(
        run_id=uuid4(),
        retry_count=1,
        stage=RunStage.DRAFT,
        key="draft:assembled",
        summary={"section_count": 2},
        completed_stages=("retrieve",),
        next_stage=None,
    )

    payload = checkpoint_store.captured[0].payload_json
    assert checkpoint_store.captured[0].checkpoint_key == "attempt-1:draft:assembled"
    assert payload is not None
    assert payload["completed_stages"] == ["retrieve"]
    assert payload["attempt"] == 2


@pytest.mark.asyncio
async def test_event_bridge_serializes_concurrent_appends() -> None:
    event_store = _ConcurrentEventStore()
    bridge = RunGraphEventBridge(
        event_store=event_store,  # type: ignore[arg-type]
        transaction_manager=_NoopTransactionManager(),
        clock=UtcRunClock(),
    )

    await asyncio.gather(
        bridge.info(
            run_id=uuid4(),
            retry_count=0,
            cancel_requested=False,
            stage=RunStage.RETRIEVE,
            key="retrieval:first",
            message="First",
            payload={},
        ),
        bridge.warning(
            run_id=uuid4(),
            retry_count=0,
            cancel_requested=False,
            stage=RunStage.RETRIEVE,
            key="retrieval:second",
            message="Second",
            payload={},
        ),
    )

    assert event_store.max_active_calls == 1


@pytest.mark.asyncio
async def test_checkpoint_bridge_serializes_concurrent_appends() -> None:
    checkpoint_store = _ConcurrentCheckpointStore()
    bridge = RunGraphCheckpointBridge(
        checkpoint_store=checkpoint_store,  # type: ignore[arg-type]
        transaction_manager=_NoopTransactionManager(),
        clock=UtcRunClock(),
    )

    await asyncio.gather(
        bridge.checkpoint(
            run_id=uuid4(),
            retry_count=0,
            stage=RunStage.RETRIEVE,
            key="retrieval:first",
            summary={"count": 1},
            completed_stages=tuple(),
            next_stage="draft",
        ),
        bridge.checkpoint(
            run_id=uuid4(),
            retry_count=0,
            stage=RunStage.RETRIEVE,
            key="retrieval:second",
            summary={"count": 2},
            completed_stages=tuple(),
            next_stage="draft",
        ),
    )

    assert checkpoint_store.max_active_calls == 1


@pytest.mark.asyncio
async def test_event_bridge_uses_isolated_session_factory_when_configured() -> None:
    session_factory = _FakeSessionFactory(SimpleNamespace(name="event-session"))
    _FakeIsolatedEventStore.created_sessions.clear()
    _FakeIsolatedEventStore.appended_messages.clear()
    bridge = RunGraphEventBridge(
        event_store=_FakeEventStore(),
        transaction_manager=_FailIfUsedTransactionManager(),
        clock=UtcRunClock(),
        session_factory=cast(Any, session_factory),
        event_store_factory=cast(Any, _FakeIsolatedEventStore),
        transaction_manager_factory=_FakeIsolatedTransactionManager,
    )

    await bridge.info(
        run_id=uuid4(),
        retry_count=0,
        cancel_requested=False,
        stage=RunStage.EVALUATE,
        key="evaluate.started",
        message="Started",
        payload={},
    )

    assert session_factory.calls == 1
    assert _FakeIsolatedEventStore.created_sessions == [session_factory.session]
    assert _FakeIsolatedEventStore.appended_messages == ["Started"]


@pytest.mark.asyncio
async def test_checkpoint_bridge_uses_isolated_session_factory_when_configured() -> None:
    session_factory = _FakeSessionFactory(SimpleNamespace(name="checkpoint-session"))
    _FakeIsolatedCheckpointStore.created_sessions.clear()
    _FakeIsolatedCheckpointStore.appended_keys.clear()
    bridge = RunGraphCheckpointBridge(
        checkpoint_store=_FakeCheckpointStore(),
        transaction_manager=_FailIfUsedTransactionManager(),
        clock=UtcRunClock(),
        session_factory=cast(Any, session_factory),
        checkpoint_store_factory=cast(Any, _FakeIsolatedCheckpointStore),
        transaction_manager_factory=_FakeIsolatedTransactionManager,
    )

    await bridge.checkpoint(
        run_id=uuid4(),
        retry_count=0,
        stage=RunStage.EVALUATE,
        key="evaluate.completed",
        summary={"section_count": 2},
        completed_stages=("retrieve", "draft"),
        next_stage="repair",
    )

    assert session_factory.calls == 1
    assert _FakeIsolatedCheckpointStore.created_sessions == [session_factory.session]
    assert _FakeIsolatedCheckpointStore.appended_keys == ["attempt-0:evaluate.completed"]


@pytest.mark.asyncio
async def test_stage_entered_maps_cancel_request_to_terminal_state() -> None:
    run = _run(cancel_requested=True)
    bridge = RunGraphRuntimeBridge(
        run_repository=_FakeRunRepository(run),
        event_store=_FakeEventStore(),
        checkpoint_store=_FakeCheckpointStore(),
        queue_backend=_FakeQueueBackend(),
        transaction_manager=_NoopTransactionManager(),
        clock=UtcRunClock(),
        queue_lease_seconds=30,
    )
    state: RunGraphState = {
        "run_id": run.id,
        "queue_item_id": uuid4(),
        "lease_token": uuid4(),
        "tenant_id": run.tenant_id,
        "conversation_id": run.conversation_id,
        "output_type": run.output_type,
        "retry_count": 0,
        "request_text": "",
        "cancel_requested": False,
        "start_stage": "retrieve",
        "completed_stages": tuple(),
        "current_stage": "retrieve",
        "latest_checkpoint_key": None,
        "latest_checkpoint_stage": None,
        "resuming": False,
    }

    entered = await bridge.stage_entered(state=state, stage=RunStage.RETRIEVE)

    assert entered is False
    assert state["terminal_status"] == "canceled"
