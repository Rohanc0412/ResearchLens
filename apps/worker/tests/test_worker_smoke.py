from researchlens_worker.create_worker import create_worker


def test_create_worker_smoke() -> None:
    worker = create_worker()
    assert worker.describe() == "researchlens-worker:phase-0"

