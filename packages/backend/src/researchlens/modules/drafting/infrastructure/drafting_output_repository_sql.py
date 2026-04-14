from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.drafting.application.ports import DraftingRepository
from researchlens.modules.drafting.domain import (
    DraftingSection,
    ReportDraft,
    SectionBrief,
    SectionDraft,
)
from researchlens.modules.drafting.infrastructure.rows import (
    DraftingReportDraftRow,
    DraftingSectionDraftRow,
    DraftingSectionEvidenceRow,
    DraftingSectionRow,
)


class SqlAlchemyDraftingRepository(DraftingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def replace_section_preparation(
        self,
        *,
        run_id: UUID,
        briefs: tuple[SectionBrief, ...],
    ) -> None:
        await self._session.execute(
            delete(DraftingSectionEvidenceRow).where(DraftingSectionEvidenceRow.run_id == run_id)
        )
        await self._session.execute(
            delete(DraftingSectionRow).where(DraftingSectionRow.run_id == run_id)
        )
        now = datetime.now(tz=UTC)
        for brief in briefs:
            row_id = uuid4()
            self._session.add(
                DraftingSectionRow(
                    id=row_id,
                    tenant_id=brief.section.tenant_id,
                    run_id=brief.section.run_id,
                    section_id=brief.section.section_id,
                    title=brief.section.title,
                    section_order=brief.section.section_order,
                    goal=brief.section.goal,
                    key_points_json=list(brief.section.key_points),
                    evidence_summary=brief.evidence_summary,
                    created_at=now,
                    updated_at=now,
                )
            )
            await self._session.flush()
            for item in brief.evidence_pack.items:
                self._session.add(
                    DraftingSectionEvidenceRow(
                        id=uuid4(),
                        section_row_id=row_id,
                        tenant_id=item.tenant_id,
                        run_id=item.run_id,
                        source_id=item.source_id,
                        chunk_id=item.chunk_id,
                        source_rank=item.source_rank,
                        chunk_index=item.chunk_index,
                        source_title=item.title,
                        excerpt_text=item.text_excerpt,
                        created_at=now,
                    )
                )
        await self._session.flush()

    async def replace_section_draft(self, *, draft: SectionDraft) -> None:
        existing = await self._session.scalar(
            select(DraftingSectionDraftRow).where(
                DraftingSectionDraftRow.run_id == draft.run_id,
                DraftingSectionDraftRow.section_id == draft.section.section_id,
            )
        )
        now = datetime.now(tz=UTC)
        if existing is None:
            self._session.add(
                DraftingSectionDraftRow(
                    id=uuid4(),
                    tenant_id=draft.tenant_id,
                    run_id=draft.run_id,
                    section_id=draft.section.section_id,
                    section_order=draft.section.section_order,
                    title=draft.section.title,
                    section_text=draft.section_text,
                    section_summary=draft.section_summary,
                    status=draft.status,
                    provider_name=draft.provider_name,
                    model_name=draft.model_name,
                    created_at=now,
                    updated_at=now,
                )
            )
        else:
            existing.section_order = draft.section.section_order
            existing.title = draft.section.title
            existing.section_text = draft.section_text
            existing.section_summary = draft.section_summary
            existing.status = draft.status
            existing.provider_name = draft.provider_name
            existing.model_name = draft.model_name
            existing.updated_at = now
        await self._session.flush()

    async def list_persisted_section_drafts(self, *, run_id: UUID) -> tuple[SectionDraft, ...]:
        rows = (
            await self._session.scalars(
                select(DraftingSectionDraftRow).where(DraftingSectionDraftRow.run_id == run_id)
            )
        ).all()
        return tuple(
            SectionDraft(
                run_id=row.run_id,
                tenant_id=row.tenant_id,
                section=DraftingSection(
                    run_id=row.run_id,
                    tenant_id=row.tenant_id,
                    section_id=row.section_id,
                    title=row.title,
                    section_order=row.section_order,
                    goal="Persisted draft section",
                    key_points=(),
                ),
                section_text=row.section_text,
                section_summary=row.section_summary,
                status=row.status,
                provider_name=row.provider_name,
                model_name=row.model_name,
            )
            for row in sorted(rows, key=lambda item: item.section_order)
        )

    async def replace_report_draft(self, *, draft: ReportDraft) -> None:
        existing = await self._session.scalar(
            select(DraftingReportDraftRow).where(DraftingReportDraftRow.run_id == draft.run_id)
        )
        now = datetime.now(tz=UTC)
        if existing is None:
            self._session.add(
                DraftingReportDraftRow(
                    id=uuid4(),
                    tenant_id=draft.tenant_id,
                    run_id=draft.run_id,
                    title=draft.title,
                    markdown_text=draft.markdown_text,
                    created_at=now,
                    updated_at=now,
                )
            )
        else:
            existing.title = draft.title
            existing.markdown_text = draft.markdown_text
            existing.updated_at = now
        await self._session.flush()
