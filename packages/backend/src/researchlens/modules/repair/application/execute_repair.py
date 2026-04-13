import asyncio
from uuid import UUID

from researchlens.modules.repair.application.dtos import (
    RepairExecutionSummary,
    RepairPassRecord,
    SectionRepairInput,
    SectionRepairOutcome,
)
from researchlens.modules.repair.application.fallback_edits import try_validated_fallback
from researchlens.modules.repair.application.output_validation import parse_repair_output
from researchlens.modules.repair.application.ports import RepairRepository, RunCancellationProbe
from researchlens.modules.repair.application.prompting import build_repair_request
from researchlens.modules.repair.domain import select_repair_inputs
from researchlens.shared.config.repair import RepairSettings
from researchlens.shared.errors import CancellationRequestedError, ValidationError
from researchlens.shared.llm.ports import StructuredGenerationClient


class RepairProgressSink:
    async def selected(self, *, section_id: str) -> None:
        return None

    async def started(self, *, section_id: str) -> None:
        return None

    async def completed(self, *, outcome: SectionRepairOutcome) -> None:
        return None


class RepairStageExecutor:
    def __init__(
        self,
        *,
        settings: RepairSettings,
        repository: RepairRepository,
        generation_client: StructuredGenerationClient,
        cancellation_probe: RunCancellationProbe,
    ) -> None:
        self._settings = settings
        self._repository = repository
        self._generation_client = generation_client
        self._cancellation_probe = cancellation_probe

    async def run(self, *, run_id: UUID, progress: RepairProgressSink) -> RepairExecutionSummary:
        inputs = await self._repository.load_inputs(run_id=run_id)
        if await self._cancellation_probe.cancel_requested(run_id=run_id):
            raise CancellationRequestedError("Repair canceled at a stage boundary.")
        tenant_id = inputs[0].tenant_id if inputs else None
        if tenant_id is None:
            return _empty_summary()
        repair_pass = await self._repository.create_pass(tenant_id=tenant_id, run_id=run_id)
        skipped = await self._record_skips(repair_pass=repair_pass, inputs=inputs)
        selected = select_repair_inputs(inputs)
        for repair_input in selected:
            await progress.selected(section_id=repair_input.section_id)
            if not repair_input.issues:
                raise ValidationError("A selected repair section must include persisted issues.")
        outcomes = await self._repair_selected(
            repair_pass=repair_pass,
            selected=selected,
            progress=progress,
        )
        await self._repository.apply_changed_sections(run_id=run_id, outcomes=outcomes)
        summary = _summary(
            repair_pass=repair_pass,
            selected=selected,
            skipped=skipped,
            outcomes=outcomes,
        )
        await self._repository.finalize_pass(repair_pass=repair_pass, summary=summary)
        return summary

    async def _record_skips(
        self,
        *,
        repair_pass: RepairPassRecord,
        inputs: tuple[SectionRepairInput, ...],
    ) -> tuple[str, ...]:
        skipped: list[str] = []
        for repair_input in inputs:
            if repair_input.repair_attempt_count >= 1 and (
                repair_input.triggered_by_low_faithfulness
                or repair_input.triggered_by_contradiction
            ):
                await self._repository.record_skipped_attempt_limit(
                    repair_pass=repair_pass,
                    repair_input=repair_input,
                )
                skipped.append(repair_input.section_id)
        return tuple(skipped)

    async def _repair_selected(
        self,
        *,
        repair_pass: RepairPassRecord,
        selected: tuple[SectionRepairInput, ...],
        progress: RepairProgressSink,
    ) -> tuple[SectionRepairOutcome, ...]:
        semaphore = asyncio.Semaphore(self._settings.max_concurrent_sections)
        tasks = [
            asyncio.create_task(
                self._repair_one(
                    repair_pass=repair_pass,
                    repair_input=item,
                    semaphore=semaphore,
                    progress=progress,
                )
            )
            for item in selected
        ]
        outcomes = await asyncio.gather(*tasks)
        return tuple(sorted(outcomes, key=lambda item: item.section_id))

    async def _repair_one(
        self,
        *,
        repair_pass: RepairPassRecord,
        repair_input: SectionRepairInput,
        semaphore: asyncio.Semaphore,
        progress: RepairProgressSink,
    ) -> SectionRepairOutcome:
        async with semaphore:
            await progress.started(section_id=repair_input.section_id)
            result_id = await self._repository.begin_section_attempt(
                repair_pass=repair_pass,
                repair_input=repair_input,
            )
            outcome = await self._model_or_fallback(result_id=result_id, repair_input=repair_input)
            await self._repository.complete_section_attempt(
                repair_result_id=result_id,
                outcome=outcome,
                original_text=repair_input.current_section_text,
                original_summary=repair_input.current_section_summary,
            )
            await progress.completed(outcome=outcome)
            return outcome

    async def _model_or_fallback(
        self,
        *,
        result_id: UUID,
        repair_input: SectionRepairInput,
    ) -> SectionRepairOutcome:
        try:
            result = await self._generation_client.generate_structured(
                build_repair_request(
                    repair_input,
                    max_output_tokens=self._settings.section_max_output_tokens,
                )
            )
            payload = parse_repair_output(data=result.data, repair_input=repair_input)
            return SectionRepairOutcome(
                repair_result_id=result_id,
                section_id=repair_input.section_id,
                action="model_repair",
                status="changed",
                changed=payload.revised_text != repair_input.current_section_text,
                revised_text=payload.revised_text,
                revised_summary=payload.revised_summary,
            )
        except Exception as exc:
            fallback = try_validated_fallback(repair_input)
            if fallback is None:
                return SectionRepairOutcome(
                    repair_result_id=result_id,
                    section_id=repair_input.section_id,
                    action="unresolved",
                    status="unresolved",
                    changed=False,
                    unresolved_reason=str(exc),
                )
            return SectionRepairOutcome(
                repair_result_id=result_id,
                section_id=repair_input.section_id,
                action="fallback_edit",
                status="changed",
                changed=True,
                revised_text=fallback[0],
                revised_summary=fallback[1],
            )


def _empty_summary() -> RepairExecutionSummary:
    return RepairExecutionSummary(
        repair_pass_id=None,
        selected_section_ids=(),
        changed_section_ids=(),
        unresolved_section_ids=(),
        skipped_section_ids=(),
        result_ids_by_section={},
    )


def _summary(
    *,
    repair_pass: RepairPassRecord,
    selected: tuple[SectionRepairInput, ...],
    skipped: tuple[str, ...],
    outcomes: tuple[SectionRepairOutcome, ...],
) -> RepairExecutionSummary:
    return RepairExecutionSummary(
        repair_pass_id=repair_pass.id,
        selected_section_ids=tuple(item.section_id for item in selected),
        changed_section_ids=tuple(item.section_id for item in outcomes if item.changed),
        unresolved_section_ids=tuple(
            item.section_id for item in outcomes if item.status == "unresolved"
        ),
        skipped_section_ids=skipped,
        result_ids_by_section={item.section_id: item.repair_result_id for item in outcomes},
    )
