import asyncio
from uuid import UUID

from researchlens.modules.evaluation.application import (
    EvaluationExecutionResult,
    EvaluationPassRecord,
    EvaluationRunInput,
    EvaluationStageSteps,
    EvaluationSummary,
)
from researchlens.modules.evaluation.application.ports import (
    EvaluationInputReader,
    EvaluationRepository,
    RunCancellationProbe,
    SectionGroundingEvaluator,
)
from researchlens.modules.evaluation.orchestration.progress import (
    EvaluationGraphCheckpointSink,
    EvaluationGraphEventSink,
    EvaluationGraphProgressWriter,
)
from researchlens.shared.config import ResearchLensSettings
from researchlens.shared.errors import CancellationRequestedError


class EvaluationGraphRuntime:
    def __init__(
        self,
        *,
        settings: ResearchLensSettings,
        input_reader: EvaluationInputReader,
        repository: EvaluationRepository,
        evaluator: SectionGroundingEvaluator,
        cancellation_probe: RunCancellationProbe,
        events: EvaluationGraphEventSink,
        checkpoints: EvaluationGraphCheckpointSink,
    ) -> None:
        if settings.llm.provider == "disabled" or not settings.llm.api_key:
            raise ValueError("Evaluation requires an enabled real LLM provider.")
        self._input_reader = input_reader
        self._events = events
        self._checkpoints = checkpoints
        self._timeout_seconds = settings.evaluation.stage_timeout_seconds
        self._progress = EvaluationGraphProgressWriter(events)
        self._steps = EvaluationStageSteps(
            settings=settings.evaluation,
            repository=repository,
            evaluator=evaluator,
            cancellation_probe=cancellation_probe,
        )

    async def load_inputs(self, *, run_id: UUID) -> EvaluationRunInput:
        await self._events.info(
            key="evaluate.started",
            message="Starting grounding evaluation",
            payload={},
        )
        return await self._input_reader.load_run_evaluation_input(run_id=run_id)

    async def create_pass(self, *, run_input: EvaluationRunInput) -> EvaluationPassRecord:
        return await self._steps.create_pass(run_input=run_input)

    async def evaluate_sections(
        self,
        *,
        run_input: EvaluationRunInput,
        evaluation_pass: EvaluationPassRecord,
    ) -> EvaluationExecutionResult:
        try:
            async with asyncio.timeout(self._timeout_seconds):
                return await self._steps.evaluate_sections(
                    run_input=run_input,
                    evaluation_pass=evaluation_pass,
                    progress=self._progress,
                )
        except Exception as exc:
            await self.handle_failure(exc=exc)
            raise

    async def persist_results(
        self,
        *,
        evaluation_pass: EvaluationPassRecord,
        section_results: EvaluationExecutionResult,
    ) -> None:
        await self._steps.persist_results(
            evaluation_pass=evaluation_pass,
            section_results=section_results.section_results,
        )

    async def finalize(
        self,
        *,
        run_input: EvaluationRunInput,
        evaluation_pass: EvaluationPassRecord,
        section_results: EvaluationExecutionResult,
    ) -> EvaluationSummary:
        summary = await self._steps.finalize(
            run_input=run_input,
            evaluation_pass=evaluation_pass,
            section_results=section_results.section_results,
        )
        await self._events.info(
            key="evaluate.summary_computed",
            message="Computed evaluation summary",
            payload=summary.model_dump(mode="json"),
        )
        await self._events.info(
            key="evaluate.completed",
            message=(
                "Evaluation completed: "
                f"{summary.sections_requiring_repair_count} sections marked for possible repair"
            ),
            payload=summary.model_dump(mode="json"),
        )
        return summary

    async def checkpoint(
        self,
        *,
        summary: EvaluationSummary,
        completed_stages: tuple[str, ...],
    ) -> None:
        payload = summary.model_dump(mode="json")
        await self._checkpoints.checkpoint(
            key="evaluate:completed",
            summary={**payload, "next_stage": "finalize"},
            completed_stages=completed_stages,
            next_stage=None,
        )

    async def handle_failure(self, *, exc: Exception) -> None:
        if isinstance(exc, CancellationRequestedError):
            return
        await self._events.warning(
            key="evaluate.failed",
            message="Evaluation failed",
            payload={"reason": str(exc)},
        )
