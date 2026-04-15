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
    TransactionManager,
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
        transaction_manager: TransactionManager,
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
            transaction_manager=transaction_manager,
        )

    async def load_inputs(
        self,
        *,
        run_id: UUID,
        section_ids: tuple[str, ...] | None = None,
        scope: str = "pipeline",
    ) -> EvaluationRunInput:
        if scope == "repair_reevaluation":
            key = "repair.reevaluation_started"
            message = "Starting targeted repair reevaluation"
        else:
            key = "evaluate.started"
            message = "Starting grounding evaluation"
        await self._events.info(key=key, message=message, payload={"scope": scope})
        return await self._input_reader.load_run_evaluation_input(
            run_id=run_id,
            section_ids=section_ids,
        )

    async def create_pass(
        self,
        *,
        run_input: EvaluationRunInput,
        scope: str = "pipeline",
    ) -> EvaluationPassRecord:
        return await self._steps.create_pass(run_input=run_input, scope=scope)

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
        event_prefix = (
            "repair.reevaluation"
            if evaluation_pass.scope == "repair_reevaluation"
            else "evaluate"
        )
        await self._events.info(
            key=f"{event_prefix}.summary_computed",
            message="Computed evaluation summary",
            payload=summary.model_dump(mode="json"),
        )
        await self._events.info(
            key=f"{event_prefix}.completed",
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
        scope: str = "pipeline",
    ) -> None:
        payload = summary.model_dump(mode="json")
        next_stage = "repair" if scope == "pipeline" else "finalize"
        await self._checkpoints.checkpoint(
            key=f"{scope}:completed",
            summary={**payload, "next_stage": next_stage},
            completed_stages=completed_stages,
            next_stage=next_stage,
        )

    async def handle_failure(self, *, exc: Exception) -> None:
        if isinstance(exc, CancellationRequestedError):
            return
        await self._events.warning(
            key="evaluate.failed",
            message="Evaluation failed",
            payload={"reason": str(exc)},
        )
