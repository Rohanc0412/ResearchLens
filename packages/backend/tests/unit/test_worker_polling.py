import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast
from uuid import uuid4

import pytest

from researchlens.modules.runs.application import ProcessRunQueueItemCommand
from researchlens.modules.runs.domain import RunQueueItem
from researchlens.shared.config import ResearchLensSettings
from researchlens.worker_polling import poll_worker_once


class _FakeTransactionManager:
    @asynccontextmanager
    async def boundary(self) -> AsyncIterator[None]:
        yield


class _ClaimOnlyQueueBackend:
    def __init__(self, queue_items: list[RunQueueItem]) -> None:
        self._queue_items = queue_items
        self.claim_calls = 0
        self.heartbeat_calls = 0
        self.heartbeat_seen = asyncio.Event()

    async def claim_available(self, **kwargs):  # type: ignore[no-untyped-def]
        self.claim_calls += 1
        return self._queue_items

    async def heartbeat(self, **kwargs):  # type: ignore[no-untyped-def]
        self.heartbeat_calls += 1
        self.heartbeat_seen.set()
        return True


class _NoopProcessor:
    def __init__(self) -> None:
        self.commands: list[ProcessRunQueueItemCommand] = []

    async def execute(self, command: ProcessRunQueueItemCommand) -> None:
        self.commands.append(command)

    async def finalize_execution_failure(
        self,
        command: ProcessRunQueueItemCommand,
        *,
        reason: str,
        error_code: str,
    ) -> None:
        return None


class _FailingProcessor(_NoopProcessor):
    def __init__(self) -> None:
        super().__init__()
        self.finalized: list[tuple[ProcessRunQueueItemCommand, str, str]] = []

    async def execute(self, command: ProcessRunQueueItemCommand) -> None:
        self.commands.append(command)
        raise RuntimeError("boom")

    async def finalize_execution_failure(
        self,
        command: ProcessRunQueueItemCommand,
        *,
        reason: str,
        error_code: str,
    ) -> None:
        self.finalized.append((command, reason, error_code))


class _BlockingProcessor(_NoopProcessor):
    def __init__(self) -> None:
        super().__init__()
        self.release = asyncio.Event()

    async def execute(self, command: ProcessRunQueueItemCommand) -> None:
        self.commands.append(command)
        await self.release.wait()


@dataclass
class _FakeRequestContext:
    transaction_manager: _FakeTransactionManager
    queue_backend: _ClaimOnlyQueueBackend
    process_run_queue_item: _NoopProcessor


class _FakeRunsRuntime:
    def __init__(
        self,
        queue_items: list[RunQueueItem],
        processor: _NoopProcessor | None = None,
    ) -> None:
        self._queue_backend = _ClaimOnlyQueueBackend(queue_items)
        self._processor = processor or _NoopProcessor()
        self.context_entries = 0

    @asynccontextmanager
    async def request_context(self) -> AsyncIterator[_FakeRequestContext]:
        self.context_entries += 1
        yield _FakeRequestContext(
            transaction_manager=_FakeTransactionManager(),
            queue_backend=self._queue_backend,
            process_run_queue_item=self._processor,
        )


def _settings() -> ResearchLensSettings:
    return cast(
        ResearchLensSettings,
        SimpleNamespace(
            queue=SimpleNamespace(
                lease_seconds=30,
                max_attempts=5,
                batch_size=2,
            )
        )
    )


def _settings_with_lease(lease_seconds: int) -> ResearchLensSettings:
    return cast(
        ResearchLensSettings,
        SimpleNamespace(
            queue=SimpleNamespace(
                lease_seconds=lease_seconds,
                max_attempts=5,
                batch_size=2,
            )
        )
    )


def _queue_item() -> RunQueueItem:
    now = datetime.now(tz=UTC)
    return RunQueueItem(
        id=uuid4(),
        tenant_id=uuid4(),
        run_id=uuid4(),
        job_type="run",
        status="leased",
        available_at=now,
        lease_token=uuid4(),
        leased_at=now,
        lease_expires_at=now,
        attempts=1,
        last_error=None,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_poll_worker_once_uses_fresh_request_context_per_claimed_item() -> None:
    runtime = _FakeRunsRuntime([_queue_item()])

    await poll_worker_once(runs_runtime=runtime, settings=_settings())

    assert runtime._queue_backend.claim_calls == 1
    assert runtime.context_entries == 2
    assert len(runtime._processor.commands) == 1


@pytest.mark.asyncio
async def test_poll_worker_once_finalizes_failure_in_fresh_request_context() -> None:
    processor = _FailingProcessor()
    runtime = _FakeRunsRuntime([_queue_item()], processor=processor)

    await poll_worker_once(runs_runtime=runtime, settings=_settings())

    assert runtime._queue_backend.claim_calls == 1
    assert runtime.context_entries == 3
    assert len(processor.commands) == 1
    assert len(processor.finalized) == 1
    _, reason, error_code = processor.finalized[0]
    assert reason == "boom"
    assert error_code == "RuntimeError"


@pytest.mark.asyncio
async def test_poll_worker_once_heartbeats_while_item_is_processing() -> None:
    processor = _BlockingProcessor()
    runtime = _FakeRunsRuntime([_queue_item()], processor=processor)
    poll_task = asyncio.create_task(
        poll_worker_once(runs_runtime=runtime, settings=_settings_with_lease(1))
    )

    await runtime._queue_backend.heartbeat_seen.wait()
    processor.release.set()
    await poll_task

    assert runtime._queue_backend.heartbeat_calls >= 1
