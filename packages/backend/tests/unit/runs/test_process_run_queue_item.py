from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from researchlens.modules.runs.application.process_run_queue_item import (
    ProcessRunQueueItemCommand,
    ProcessRunQueueItemUseCase,
)
from researchlens.modules.runs.domain import Run


class _FakeRunRepository:
    def __init__(self, run: Run) -> None:
        self._run = run
        self.reads = 0

    async def get_by_id(self, *, run_id):  # type: ignore[no-untyped-def]
        self.reads += 1
        return self._run


class _FakeQueueBackend:
    def __init__(self) -> None:
        self.completed = False

    async def complete(self, **kwargs):  # type: ignore[no-untyped-def]
        self.completed = True
        return True


class _FakeTransactionManager:
    @asynccontextmanager
    async def boundary(self) -> AsyncIterator[None]:
        yield


class _FakeTerminalMutations:
    def __init__(self) -> None:
        self.finalized = False
        self.canceled = False
        self.reason: str | None = None
        self.error_code: str | None = None

    async def finalize_failure(self, *, run: Run, reason: str, error_code: str) -> None:
        self.finalized = True
        self.reason = reason
        self.error_code = error_code

    async def finalize_cancel(self, *, run: Run) -> None:
        self.canceled = True


class _FailingOrchestrator:
    async def execute(self, *, run, queue_item_id, lease_token):  # type: ignore[no-untyped-def]
        raise RuntimeError("boom")


class _FakeEventStore:
    pass


def _build_run(*, cancel_requested: bool = False) -> Run:
    now = datetime.now(tz=UTC)
    run = Run.create(
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
    )
    if cancel_requested:
        run = run.replace_values(cancel_requested_at=now, updated_at=now)
    return run


def _build_use_case(
    run: Run,
) -> tuple[ProcessRunQueueItemUseCase, _FakeRunRepository, _FakeQueueBackend]:
    repository = _FakeRunRepository(run)
    queue_backend = _FakeQueueBackend()
    use_case = ProcessRunQueueItemUseCase(
        run_repository=repository,  # type: ignore[arg-type]
        event_store=_FakeEventStore(),  # type: ignore[arg-type]
        queue_backend=queue_backend,  # type: ignore[arg-type]
        transaction_manager=_FakeTransactionManager(),
        run_orchestrator=_FailingOrchestrator(),
    )
    return use_case, repository, queue_backend


@pytest.mark.asyncio
async def test_process_run_queue_item_execute_finalizes_orchestrator_failure() -> None:
    run = _build_run()
    use_case, repository, queue_backend = _build_use_case(run)
    terminal_mutations = _FakeTerminalMutations()
    use_case._terminal_mutations = terminal_mutations  # type: ignore[assignment]

    await use_case.execute(
        ProcessRunQueueItemCommand(
            queue_item_id=uuid4(),
            lease_token=uuid4(),
            run_id=run.id,
        )
    )

    assert repository.reads == 2
    assert terminal_mutations.finalized is True
    assert terminal_mutations.reason == "boom"
    assert terminal_mutations.error_code == "RuntimeError"
    assert queue_backend.completed is True


@pytest.mark.asyncio
async def test_finalize_execution_failure_records_failure_and_acks_queue_item() -> None:
    run = _build_run()
    use_case, repository, queue_backend = _build_use_case(run)
    terminal_mutations = _FakeTerminalMutations()
    use_case._terminal_mutations = terminal_mutations  # type: ignore[assignment]

    await use_case.finalize_execution_failure(
        ProcessRunQueueItemCommand(
            queue_item_id=uuid4(),
            lease_token=uuid4(),
            run_id=run.id,
        ),
        reason="x" * 5000,
        error_code="RuntimeError",
    )

    assert repository.reads == 1
    assert terminal_mutations.finalized is True
    assert terminal_mutations.reason is not None
    assert len(terminal_mutations.reason) == 4000
    assert terminal_mutations.error_code == "RuntimeError"
    assert queue_backend.completed is True


@pytest.mark.asyncio
async def test_finalize_execution_failure_respects_existing_cancel_request() -> None:
    run = _build_run(cancel_requested=True)
    use_case, repository, queue_backend = _build_use_case(run)
    terminal_mutations = _FakeTerminalMutations()
    use_case._terminal_mutations = terminal_mutations  # type: ignore[assignment]

    await use_case.finalize_execution_failure(
        ProcessRunQueueItemCommand(
            queue_item_id=uuid4(),
            lease_token=uuid4(),
            run_id=run.id,
        ),
        reason="boom",
        error_code="RuntimeError",
    )

    assert repository.reads == 1
    assert terminal_mutations.canceled is True
    assert terminal_mutations.finalized is False
    assert queue_backend.completed is True
