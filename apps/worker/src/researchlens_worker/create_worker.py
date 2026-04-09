from researchlens_worker.bootstrap import build_worker_bootstrap_state
from researchlens_worker.worker_runtime import WorkerRuntime


def create_worker() -> WorkerRuntime:
    return WorkerRuntime(state=build_worker_bootstrap_state())
