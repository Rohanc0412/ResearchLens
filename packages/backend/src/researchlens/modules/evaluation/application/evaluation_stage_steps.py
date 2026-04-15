import asyncio
from dataclasses import dataclass

from researchlens.modules.evaluation.application.dtos import (
    EvaluationPassRecord,
    EvaluationRunInput,
    EvaluationSectionInput,
    EvaluationSummary,
    SectionEvaluationResult,
)
from researchlens.modules.evaluation.application.evaluate_section import evaluate_section
from researchlens.modules.evaluation.application.finalize_evaluation_pass import summarize_results
from researchlens.modules.evaluation.application.ports import (
    EvaluationRepository,
    RunCancellationProbe,
    SectionGroundingEvaluator,
    TransactionManager,
)
from researchlens.shared.config.evaluation import EvaluationSettings
from researchlens.shared.errors import CancellationRequestedError


@dataclass(frozen=True, slots=True)
class EvaluationExecutionResult:
    section_results: tuple[SectionEvaluationResult, ...]


class EvaluationProgressSink:
    async def section_started(self, *, section_title: str) -> None:
        return None

    async def section_completed(self, *, section_title: str) -> None:
        return None


class EvaluationStageSteps:
    def __init__(
        self,
        *,
        settings: EvaluationSettings,
        repository: EvaluationRepository,
        evaluator: SectionGroundingEvaluator,
        cancellation_probe: RunCancellationProbe,
        transaction_manager: TransactionManager,
    ) -> None:
        self._settings = settings
        self._repository = repository
        self._evaluator = evaluator
        self._cancellation_probe = cancellation_probe
        self._transaction_manager = transaction_manager
        self._cancellation_lock = asyncio.Lock()

    async def create_pass(
        self,
        *,
        run_input: EvaluationRunInput,
        scope: str = "pipeline",
    ) -> EvaluationPassRecord:
        async with self._transaction_manager.boundary():
            return await self._repository.create_pass(
                tenant_id=run_input.tenant_id,
                run_id=run_input.run_id,
                scope=scope,
            )

    async def evaluate_sections(
        self,
        *,
        run_input: EvaluationRunInput,
        evaluation_pass: EvaluationPassRecord,
        progress: EvaluationProgressSink | None = None,
    ) -> EvaluationExecutionResult:
        await self._raise_if_canceled(run_input=run_input)
        semaphore = asyncio.Semaphore(self._settings.max_concurrent_sections)
        tasks = [
            asyncio.create_task(
                self._evaluate_one_section(
                    run_input=run_input,
                    evaluation_pass=evaluation_pass,
                    section=section,
                    semaphore=semaphore,
                    progress=progress,
                )
            )
            for section in run_input.sections
        ]
        section_results = await asyncio.gather(*tasks)
        await self._raise_if_canceled(run_input=run_input)
        return EvaluationExecutionResult(
            section_results=tuple(
                sorted(section_results, key=lambda item: (item.section_order, item.section_id))
            )
        )

    async def persist_results(
        self,
        *,
        evaluation_pass: EvaluationPassRecord,
        section_results: tuple[SectionEvaluationResult, ...],
    ) -> None:
        async with self._transaction_manager.boundary():
            await self._repository.persist_section_results(
                evaluation_pass=evaluation_pass,
                section_results=section_results,
            )

    async def finalize(
        self,
        *,
        evaluation_pass: EvaluationPassRecord,
        run_input: EvaluationRunInput,
        section_results: tuple[SectionEvaluationResult, ...],
    ) -> EvaluationSummary:
        summary = summarize_results(
            evaluation_pass_id=evaluation_pass.id,
            section_count=len(run_input.sections),
            section_results=section_results,
        )
        async with self._transaction_manager.boundary():
            await self._repository.finalize_pass(evaluation_pass=evaluation_pass, summary=summary)
        return summary

    async def _evaluate_one_section(
        self,
        *,
        run_input: EvaluationRunInput,
        evaluation_pass: EvaluationPassRecord,
        section: EvaluationSectionInput,
        semaphore: asyncio.Semaphore,
        progress: EvaluationProgressSink | None,
    ) -> SectionEvaluationResult:
        async with semaphore:
            await self._raise_if_canceled(run_input=run_input)
            section_title = getattr(section, "section_title", "section")
            if progress is not None:
                await progress.section_started(section_title=str(section_title))
            result = await evaluate_section(
                evaluation_pass_id=evaluation_pass.id,
                evaluator=self._evaluator,
                run_input=run_input,
                section=section,
            )
            if progress is not None:
                await progress.section_completed(section_title=str(section_title))
            return result

    async def _raise_if_canceled(self, *, run_input: EvaluationRunInput) -> None:
        async with self._cancellation_lock:
            canceled = await self._cancellation_probe.cancel_requested(run_id=run_input.run_id)
        if canceled:
            raise CancellationRequestedError("Evaluation canceled at a stage boundary.")
