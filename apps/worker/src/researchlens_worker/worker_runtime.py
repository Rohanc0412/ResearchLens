import asyncio

from researchlens.worker_composition import poll_worker_once
from researchlens_worker.bootstrap import WorkerBootstrapState


class WorkerRuntime:
    def __init__(self, state: WorkerBootstrapState) -> None:
        self._state = state
        self._stop_event = asyncio.Event()

    def describe(self) -> str:
        settings = self._state.settings
        return f"{settings.app.worker_name}:{settings.app.phase}:{settings.app.environment}"

    async def run(self) -> None:
        settings = self._state.settings.queue
        try:
            while not self._stop_event.is_set():
                await poll_worker_once(
                    runs_runtime=self._state.runs_runtime,
                    settings=self._state.settings,
                )
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=settings.poll_interval_seconds,
                    )
                except TimeoutError:
                    continue
        finally:
            await self.shutdown()

    def stop(self) -> None:
        self._stop_event.set()

    async def shutdown(self) -> None:
        await self._state.database.dispose()
