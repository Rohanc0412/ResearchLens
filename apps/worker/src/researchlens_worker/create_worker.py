from researchlens_worker.bootstrap import WorkerBootstrapConfig
from researchlens_worker.worker_runtime import WorkerRuntime


def create_worker() -> WorkerRuntime:
    return WorkerRuntime(config=WorkerBootstrapConfig())

