import asyncio

from pytest import MonkeyPatch

from researchlens_worker.create_worker import create_worker


def test_worker_startup_smoke(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    worker = create_worker()

    assert worker.describe() == "researchlens-worker:phase-2:test"
    asyncio.run(worker.shutdown())
