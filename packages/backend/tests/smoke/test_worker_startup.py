import asyncio

from pytest import MonkeyPatch

from researchlens.shared.db import metadata
from researchlens_worker.create_worker import create_worker


def test_worker_startup_smoke(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    worker = create_worker()

    assert worker.describe() == "researchlens-worker:phase-8:test"
    assert {"projects", "conversations", "messages", "runs"}.issubset(metadata.tables)
    asyncio.run(worker.shutdown())
