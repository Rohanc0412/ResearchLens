import asyncio
from dataclasses import asdict
from uuid import UUID

from researchlens.modules.drafting.application.drafting_stage_steps import (
    DraftingPreparationResult,
    DraftingRunResult,
    DraftingStageSteps,
)
from researchlens.modules.drafting.application.ports import (
    DraftingRepository,
    DraftingRunInputReader,
    RunCancellationProbe,
)
from researchlens.modules.drafting.orchestration.progress import (
    DraftingGraphCheckpointSink,
    DraftingGraphEventSink,
    DraftingGraphProgressWriter,
)
from researchlens.shared.config import ResearchLensSettings
from researchlens.shared.errors import CancellationRequestedError
from researchlens.shared.llm.factory import build_llm_client
from researchlens.shared.llm.ports import StructuredGenerationClient


class DraftingGraphRuntime:
    def __init__(
        self,
        *,
        settings: ResearchLensSettings,
        input_reader: DraftingRunInputReader,
        repository: DraftingRepository,
        cancellation_probe: RunCancellationProbe,
        events: DraftingGraphEventSink,
        checkpoints: DraftingGraphCheckpointSink,
        generation_client: StructuredGenerationClient | None = None,
    ) -> None:
        if settings.llm.provider == "disabled" or not settings.llm.api_key:
            raise ValueError("Drafting requires an enabled real LLM provider.")
        self._input_reader = input_reader
        self._events = events
        self._checkpoints = checkpoints
        self._timeout_seconds = settings.drafting.stage_timeout_seconds
        self._progress = DraftingGraphProgressWriter(events)
        self._steps = DraftingStageSteps(
            settings=settings.drafting,
            repository=repository,
            generation_client=generation_client or build_llm_client(settings.llm),
            cancellation_probe=cancellation_probe,
            provider_name=settings.llm.provider,
        )

    async def prepare(self, *, run_id: UUID) -> DraftingPreparationResult:
        await self._events.info(
            key="draft.preparing",
            message="Draft preparation started",
            payload={},
        )
        draft_input = await self._input_reader.load_run_drafting_input(run_id=run_id)
        return await self._steps.prepare(draft_input=draft_input, progress=self._progress)

    async def draft_sections(self, *, prepared: DraftingPreparationResult) -> None:
        async with asyncio.timeout(self._timeout_seconds):
            await self._steps.draft_sections(briefs=prepared.briefs, progress=self._progress)

    async def assemble(
        self,
        *,
        prepared: DraftingPreparationResult,
        completed_stages: tuple[str, ...],
    ) -> DraftingRunResult:
        result = await self._steps.assemble_report(draft_input=prepared.draft_input)
        summary = asdict(result)
        await self._checkpoints.checkpoint(
            key="draft:assembled",
            summary=summary,
            completed_stages=completed_stages,
            next_stage=None,
        )
        await self._events.info(
            key="draft.report_assembled",
            message="Draft report assembled",
            payload=summary,
        )
        return result

    async def handle_failure(self, *, exc: Exception) -> None:
        if isinstance(exc, CancellationRequestedError):
            return
        await self._events.warning(
            key="draft.failed",
            message="Draft stage failed",
            payload={"reason": str(exc)},
        )
