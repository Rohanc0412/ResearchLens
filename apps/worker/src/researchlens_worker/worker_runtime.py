from researchlens_worker.bootstrap import WorkerBootstrapState


class WorkerRuntime:
    def __init__(self, state: WorkerBootstrapState) -> None:
        self._state = state

    def describe(self) -> str:
        settings = self._state.settings
        return (
            f"{settings.app.worker_name}:"
            f"{settings.app.phase}:"
            f"{settings.app.environment}"
        )

    async def shutdown(self) -> None:
        await self._state.database.dispose()
