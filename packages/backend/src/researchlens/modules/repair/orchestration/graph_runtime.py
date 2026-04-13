import asyncio
from uuid import UUID

from researchlens.modules.repair.application import RepairExecutionSummary, RepairStageExecutor
from researchlens.modules.repair.application.ports import RepairRepository, RunCancellationProbe
from researchlens.modules.repair.orchestration.progress import (
    RepairGraphCheckpointSink,
    RepairGraphEventSink,
    RepairGraphProgressWriter,
)
from researchlens.shared.config import ResearchLensSettings
from researchlens.shared.errors import CancellationRequestedError
from researchlens.shared.llm.ports import StructuredGenerationClient


class RepairGraphRuntime:
    def __init__(
        self,
        *,
        settings: ResearchLensSettings,
        repository: RepairRepository,
        generation_client: StructuredGenerationClient,
        cancellation_probe: RunCancellationProbe,
        events: RepairGraphEventSink,
        checkpoints: RepairGraphCheckpointSink,
    ) -> None:
        if settings.llm.provider == "disabled" or not settings.llm.api_key:
            raise ValueError("Repair requires an enabled real LLM provider.")
        self._events = events
        self._checkpoints = checkpoints
        self._timeout_seconds = settings.repair.stage_timeout_seconds
        self._executor = RepairStageExecutor(
            settings=settings.repair,
            repository=repository,
            generation_client=generation_client,
            cancellation_probe=cancellation_probe,
        )
        self._progress = RepairGraphProgressWriter(events)

    async def repair(self, *, run_id: UUID) -> RepairExecutionSummary:
        await self._events.info(key="repair.started", message="Starting repair", payload={})
        try:
            async with asyncio.timeout(self._timeout_seconds):
                summary = await self._executor.run(run_id=run_id, progress=self._progress)
        except Exception as exc:
            await self.handle_failure(exc=exc)
            raise
        await self._events.info(
            key="repair.completed",
            message="Repair completed",
            payload=summary.model_dump(mode="json"),
        )
        return summary

    async def checkpoint(
        self,
        *,
        summary: RepairExecutionSummary,
        completed_stages: tuple[str, ...],
    ) -> None:
        await self._checkpoints.checkpoint(
            key="repair:completed",
            summary={**summary.model_dump(mode="json"), "next_stage": "evaluate"},
            completed_stages=completed_stages,
            next_stage="evaluate",
        )

    async def handle_failure(self, *, exc: Exception) -> None:
        if isinstance(exc, CancellationRequestedError):
            return
        await self._events.warning(
            key="repair.failed",
            message="Repair failed",
            payload={"reason": str(exc)},
        )
