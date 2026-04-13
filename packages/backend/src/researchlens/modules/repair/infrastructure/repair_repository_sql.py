from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.repair.application.dtos import (
    RepairExecutionSummary,
    RepairPassRecord,
    RepairReadSummary,
    SectionRepairInput,
    SectionRepairOutcome,
)
from researchlens.modules.repair.infrastructure.repair_input_loader_sql import RepairInputLoader
from researchlens.modules.repair.infrastructure.repair_result_writer_sql import RepairResultWriter
from researchlens.modules.repair.infrastructure.repair_row_mapping import read_section
from researchlens.modules.repair.infrastructure.rows import RepairPassRow, RepairResultRow


class SqlAlchemyRepairRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._inputs = RepairInputLoader(session)
        self._writer = RepairResultWriter(session)

    async def load_inputs(self, *, run_id: UUID) -> tuple[SectionRepairInput, ...]:
        return await self._inputs.load_inputs(run_id=run_id)

    async def create_pass(self, *, tenant_id: UUID, run_id: UUID) -> RepairPassRecord:
        return await self._writer.create_pass(tenant_id=tenant_id, run_id=run_id)

    async def record_skipped_attempt_limit(
        self,
        *,
        repair_pass: RepairPassRecord,
        repair_input: SectionRepairInput,
    ) -> UUID:
        return await self._writer.add_result(
            repair_pass=repair_pass,
            repair_input=repair_input,
            status="skipped_attempt_limit",
            action="skipped_attempt_limit",
            increment_attempt=False,
        )

    async def begin_section_attempt(
        self,
        *,
        repair_pass: RepairPassRecord,
        repair_input: SectionRepairInput,
    ) -> UUID:
        return await self._writer.add_result(
            repair_pass=repair_pass,
            repair_input=repair_input,
            status="attempting",
            action="attempting",
            increment_attempt=True,
        )

    async def complete_section_attempt(
        self,
        *,
        repair_result_id: UUID,
        outcome: SectionRepairOutcome,
        original_text: str,
        original_summary: str,
    ) -> None:
        await self._writer.complete_section_attempt(
            repair_result_id=repair_result_id,
            outcome=outcome,
            original_text=original_text,
            original_summary=original_summary,
        )

    async def finalize_pass(
        self,
        *,
        repair_pass: RepairPassRecord,
        summary: RepairExecutionSummary,
    ) -> None:
        await self._writer.finalize_pass(repair_pass=repair_pass, summary=summary)

    async def apply_changed_sections(
        self,
        *,
        run_id: UUID,
        outcomes: tuple[SectionRepairOutcome, ...],
    ) -> None:
        await self._writer.apply_changed_sections(run_id=run_id, outcomes=outcomes)

    async def link_reevaluation_pass(
        self,
        *,
        run_id: UUID,
        changed_section_ids: tuple[str, ...],
        reevaluation_pass_id: UUID,
    ) -> None:
        await self._writer.link_reevaluation_pass(
            run_id=run_id,
            changed_section_ids=changed_section_ids,
            reevaluation_pass_id=reevaluation_pass_id,
        )

    async def latest_summary(self, *, tenant_id: UUID, run_id: UUID) -> RepairReadSummary | None:
        repair_pass = await self._latest_repair_pass(tenant_id=tenant_id, run_id=run_id)
        if repair_pass is None:
            return None
        rows = (
            await self._session.scalars(
                select(RepairResultRow)
                .where(RepairResultRow.repair_pass_id == repair_pass.id)
                .order_by(RepairResultRow.section_order.asc(), RepairResultRow.section_id.asc())
            )
        ).all()
        return RepairReadSummary(
            repair_pass_id=repair_pass.id,
            run_id=run_id,
            status=repair_pass.status,
            selected_count=len(repair_pass.selected_section_ids_json),
            changed_count=len(repair_pass.changed_section_ids_json),
            unresolved_count=len(repair_pass.unresolved_section_ids_json),
            sections=tuple(read_section(row) for row in rows),
        )

    async def _latest_repair_pass(self, *, tenant_id: UUID, run_id: UUID) -> RepairPassRow | None:
        return cast(
            RepairPassRow | None,
            await self._session.scalar(
                select(RepairPassRow)
                .where(RepairPassRow.tenant_id == tenant_id, RepairPassRow.run_id == run_id)
                .order_by(RepairPassRow.pass_index.desc())
                .limit(1)
            ),
        )
