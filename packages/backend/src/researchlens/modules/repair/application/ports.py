from typing import Protocol
from uuid import UUID

from researchlens.modules.repair.application.dtos import (
    RepairExecutionSummary,
    RepairPassRecord,
    RepairReadSummary,
    SectionRepairInput,
    SectionRepairOutcome,
)


class RepairRepository(Protocol):
    async def load_inputs(self, *, run_id: UUID) -> tuple[SectionRepairInput, ...]: ...

    async def create_pass(self, *, tenant_id: UUID, run_id: UUID) -> RepairPassRecord: ...

    async def record_skipped_attempt_limit(
        self,
        *,
        repair_pass: RepairPassRecord,
        repair_input: SectionRepairInput,
    ) -> UUID: ...

    async def begin_section_attempt(
        self,
        *,
        repair_pass: RepairPassRecord,
        repair_input: SectionRepairInput,
    ) -> UUID: ...

    async def complete_section_attempt(
        self,
        *,
        repair_result_id: UUID,
        outcome: SectionRepairOutcome,
        original_text: str,
        original_summary: str,
    ) -> None: ...

    async def finalize_pass(
        self,
        *,
        repair_pass: RepairPassRecord,
        summary: RepairExecutionSummary,
    ) -> None: ...

    async def apply_changed_sections(
        self,
        *,
        run_id: UUID,
        outcomes: tuple[SectionRepairOutcome, ...],
    ) -> None: ...

    async def link_reevaluation_pass(
        self,
        *,
        run_id: UUID,
        changed_section_ids: tuple[str, ...],
        reevaluation_pass_id: UUID,
    ) -> None: ...

    async def latest_summary(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
    ) -> RepairReadSummary | None: ...


class RunCancellationProbe(Protocol):
    async def cancel_requested(self, *, run_id: UUID) -> bool: ...
