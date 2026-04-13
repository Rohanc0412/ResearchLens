from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import Table, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.repair.application.dtos import (
    RepairExecutionSummary,
    RepairPassRecord,
    SectionRepairInput,
    SectionRepairOutcome,
)
from researchlens.modules.repair.infrastructure.repair_row_mapping import (
    assemble_markdown,
    result_row,
)
from researchlens.modules.repair.infrastructure.rows import (
    RepairFallbackEditRow,
    RepairPassRow,
    RepairResultRow,
)
from researchlens.shared.db import metadata


class RepairResultWriter:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_pass(self, *, tenant_id: UUID, run_id: UUID) -> RepairPassRecord:
        max_pass = await self._session.scalar(
            select(func.max(RepairPassRow.pass_index)).where(
                RepairPassRow.tenant_id == tenant_id,
                RepairPassRow.run_id == run_id,
            )
        )
        now = datetime.now(tz=UTC)
        row = _repair_pass_row(
            tenant_id=tenant_id,
            run_id=run_id,
            pass_index=int(max_pass or 0) + 1,
            now=now,
        )
        self._session.add(row)
        await self._session.flush()
        return RepairPassRecord(
            id=row.id,
            tenant_id=row.tenant_id,
            run_id=row.run_id,
            pass_index=row.pass_index,
            status=row.status,
        )

    async def add_result(
        self,
        *,
        repair_pass: RepairPassRecord,
        repair_input: SectionRepairInput,
        status: str,
        action: str,
        increment_attempt: bool,
    ) -> UUID:
        now = datetime.now(tz=UTC)
        result_id = uuid4()
        self._session.add(result_row(result_id, repair_pass, repair_input, status, action, now))
        if increment_attempt:
            await self._increment_attempt(repair_input=repair_input, now=now)
        await self._session.flush()
        return result_id

    async def complete_section_attempt(
        self,
        *,
        repair_result_id: UUID,
        outcome: SectionRepairOutcome,
        original_text: str,
        original_summary: str,
    ) -> None:
        row = await self._session.get(RepairResultRow, repair_result_id)
        if row is None:
            return
        now = datetime.now(tz=UTC)
        row.status = outcome.status
        row.action = outcome.action
        row.changed = outcome.changed
        row.original_text = original_text
        row.original_summary = original_summary
        row.revised_text = outcome.revised_text
        row.revised_summary = outcome.revised_summary
        row.unresolved_reason = outcome.unresolved_reason
        row.validation_summary_json = {"changed": outcome.changed, "action": outcome.action}
        row.completed_at = now
        row.updated_at = now
        if outcome.action == "fallback_edit" and outcome.revised_text is not None:
            self._session.add(_fallback_row(row.id, original_text, outcome.revised_text, now))
        await self._session.flush()

    async def finalize_pass(
        self,
        *,
        repair_pass: RepairPassRecord,
        summary: RepairExecutionSummary,
    ) -> None:
        row = await self._session.get(RepairPassRow, repair_pass.id)
        if row is None:
            return
        now = datetime.now(tz=UTC)
        row.status = "completed"
        row.selected_section_ids_json = list(summary.selected_section_ids)
        row.changed_section_ids_json = list(summary.changed_section_ids)
        row.unresolved_section_ids_json = list(summary.unresolved_section_ids)
        row.skipped_section_ids_json = list(summary.skipped_section_ids)
        row.completed_at = now
        row.updated_at = now
        await self._session.flush()

    async def apply_changed_sections(
        self,
        *,
        run_id: UUID,
        outcomes: tuple[SectionRepairOutcome, ...],
    ) -> None:
        for outcome in outcomes:
            if outcome.changed and outcome.revised_text and outcome.revised_summary:
                await self._update_section_draft(run_id=run_id, outcome=outcome)
        await self._reassemble_report(run_id=run_id)
        await self._session.flush()

    async def link_reevaluation_pass(
        self,
        *,
        run_id: UUID,
        changed_section_ids: tuple[str, ...],
        reevaluation_pass_id: UUID,
    ) -> None:
        rows = (
            await self._session.scalars(
                select(RepairResultRow).where(
                    RepairResultRow.run_id == run_id,
                    RepairResultRow.section_id.in_(changed_section_ids),
                    RepairResultRow.changed.is_(True),
                )
            )
        ).all()
        for row in rows:
            row.reevaluation_pass_id = reevaluation_pass_id
            row.updated_at = datetime.now(tz=UTC)
        await self._session.flush()

    async def _increment_attempt(self, *, repair_input: SectionRepairInput, now: datetime) -> None:
        section = _table("evaluation_section_results")
        row = await self._session.execute(
            select(section).where(section.c.id == repair_input.evaluation_section_result_id)
        )
        existing = row.mappings().first()
        if existing is not None:
            await self._session.execute(
                section.update()
                .where(section.c.id == repair_input.evaluation_section_result_id)
                .values(
                    repair_attempt_count=int(existing["repair_attempt_count"]) + 1,
                    updated_at=now,
                )
            )

    async def _update_section_draft(
        self,
        *,
        run_id: UUID,
        outcome: SectionRepairOutcome,
    ) -> None:
        draft = _table("drafting_section_drafts")
        await self._session.execute(
            draft.update()
            .where(draft.c.run_id == run_id, draft.c.section_id == outcome.section_id)
            .values(
                section_text=outcome.revised_text,
                section_summary=outcome.revised_summary,
                status=outcome.action,
                updated_at=datetime.now(tz=UTC),
            )
        )

    async def _reassemble_report(self, *, run_id: UUID) -> None:
        report = _table("drafting_report_drafts")
        drafts = _table("drafting_section_drafts")
        rows = (
            await self._session.execute(
                select(drafts).where(drafts.c.run_id == run_id).order_by(drafts.c.section_order)
            )
        ).mappings().all()
        existing = (
            await self._session.execute(select(report).where(report.c.run_id == run_id))
        ).mappings().first()
        if existing is not None:
            markdown = assemble_markdown(
                title=str(existing["title"]),
                rows=cast(Any, rows),
            )
            await self._session.execute(
                report.update()
                .where(report.c.run_id == run_id)
                .values(markdown_text=markdown, updated_at=datetime.now(tz=UTC))
            )


def _table(name: str) -> Table:
    return metadata.tables[name]


def _repair_pass_row(
    *,
    tenant_id: UUID,
    run_id: UUID,
    pass_index: int,
    now: datetime,
) -> RepairPassRow:
    return RepairPassRow(
        id=uuid4(),
        tenant_id=tenant_id,
        run_id=run_id,
        pass_index=pass_index,
        status="running",
        selected_section_ids_json=[],
        changed_section_ids_json=[],
        unresolved_section_ids_json=[],
        skipped_section_ids_json=[],
        started_at=now,
        completed_at=None,
        created_at=now,
        updated_at=now,
    )


def _fallback_row(
    repair_result_id: UUID,
    before_text: str,
    after_text: str,
    now: datetime,
) -> RepairFallbackEditRow:
    return RepairFallbackEditRow(
        id=uuid4(),
        repair_result_id=repair_result_id,
        edit_kind="targeted_sentence_removal",
        before_text=before_text,
        after_text=after_text,
        metadata_json={"validated": True},
        created_at=now,
    )
