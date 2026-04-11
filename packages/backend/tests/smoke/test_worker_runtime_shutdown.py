import asyncio
from types import SimpleNamespace
from typing import cast

import pytest

from researchlens_worker.bootstrap import WorkerBootstrapState
from researchlens_worker.worker_runtime import WorkerRuntime


@pytest.mark.asyncio
async def test_worker_runtime_stop_exits_poll_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    poll_count = 0

    async def fake_poll_worker_once(*, runs_runtime: object, settings: object) -> None:
        nonlocal poll_count
        poll_count += 1

    class FakeDatabase:
        def __init__(self) -> None:
            self.disposed = False

        async def dispose(self) -> None:
            self.disposed = True

    database = FakeDatabase()
    state = cast(
        WorkerBootstrapState,
        SimpleNamespace(
            settings=SimpleNamespace(
                app=SimpleNamespace(
                    worker_name="researchlens-worker",
                    phase="phase-5",
                    environment="test",
                ),
                queue=SimpleNamespace(poll_interval_seconds=0.01),
            ),
            runs_runtime=object(),
            database=database,
        ),
    )
    worker = WorkerRuntime(state=state)
    monkeypatch.setattr(
        "researchlens_worker.worker_runtime.poll_worker_once",
        fake_poll_worker_once,
    )

    task = asyncio.create_task(worker.run())
    await asyncio.sleep(0.03)
    worker.stop()
    await task

    assert poll_count >= 1
    assert database.disposed is True
