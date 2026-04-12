from uuid import UUID

from researchlens.modules.drafting.application.drafting_stage_steps import (
    DraftingRunResult,
    DraftingStageSteps,
    _normalize_structured_data,
)
from researchlens.modules.drafting.application.ports import (
    DraftingGenerationClient,
    DraftingProgressSink,
    DraftingRepository,
    DraftingRunInputReader,
    RunCancellationProbe,
)
from researchlens.shared.config.drafting import DraftingSettings


class RunDraftingStageUseCase:
    def __init__(
        self,
        *,
        settings: DraftingSettings,
        input_reader: DraftingRunInputReader,
        repository: DraftingRepository,
        generation_client: DraftingGenerationClient,
        cancellation_probe: RunCancellationProbe,
        provider_name: str,
    ) -> None:
        self._input_reader = input_reader
        self._steps = DraftingStageSteps(
            settings=settings,
            repository=repository,
            generation_client=generation_client,
            cancellation_probe=cancellation_probe,
            provider_name=provider_name,
        )

    async def execute(
        self,
        *,
        run_id: UUID,
        progress: DraftingProgressSink | None = None,
    ) -> DraftingRunResult:
        draft_input = await self._input_reader.load_run_drafting_input(run_id=run_id)
        prepared = await self._steps.prepare(draft_input=draft_input, progress=progress)
        await self._steps.draft_sections(briefs=prepared.briefs, progress=progress)
        return await self._steps.assemble_report(draft_input=prepared.draft_input)


__all__ = ["DraftingRunResult", "RunDraftingStageUseCase", "_normalize_structured_data"]
