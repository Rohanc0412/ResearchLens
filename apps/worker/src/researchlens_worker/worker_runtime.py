from researchlens_worker.bootstrap import WorkerBootstrapConfig


class WorkerRuntime:
    def __init__(self, config: WorkerBootstrapConfig) -> None:
        self._config = config

    def describe(self) -> str:
        return f"{self._config.app_name}:{self._config.phase}"

