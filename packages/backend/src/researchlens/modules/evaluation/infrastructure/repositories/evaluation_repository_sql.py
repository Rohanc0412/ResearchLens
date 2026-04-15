from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.evaluation.application.dtos import (
    EvaluationIssuePayload,
    EvaluationPassRecord,
    EvaluationSummary,
    RepairCandidatePayload,
    SectionEvaluationResult,
)
from researchlens.modules.evaluation.domain import MAX_REPAIRS_PER_SECTION
from researchlens.modules.evaluation.infrastructure.repositories.evaluation_mappers import (
    issue_payload,
)
from researchlens.modules.evaluation.infrastructure.repositories.evaluation_queries import (
    latest_completed_pass,
)
from researchlens.modules.evaluation.infrastructure.repositories.evaluation_writes import (
    add_claim_rows,
    add_issue_rows,
    add_section_result_row,
)
from researchlens.modules.evaluation.infrastructure.rows import (
    EvaluationIssueRow,
    EvaluationPassRow,
    EvaluationSectionResultRow,
)


class SqlAlchemyEvaluationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_pass(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
        scope: str,
    ) -> EvaluationPassRecord:
        max_pass = await self._session.scalar(
            select(func.max(EvaluationPassRow.pass_index)).where(
                EvaluationPassRow.tenant_id == tenant_id,
                EvaluationPassRow.run_id == run_id,
                EvaluationPassRow.scope == scope,
            )
        )
        now = datetime.now(tz=UTC)
        row = EvaluationPassRow(
            id=uuid4(),
            tenant_id=tenant_id,
            run_id=run_id,
            scope=scope,
            pass_index=int(max_pass or 0) + 1,
            status="running",
            section_count=0,
            evaluated_section_count=0,
            issue_count=0,
            sections_requiring_repair_count=0,
            quality_pct=0.0,
            unsupported_claim_rate=0.0,
            pass_rate=0.0,
            ragas_faithfulness_pct=0.0,
            issues_by_type_json={},
            started_at=now,
            completed_at=None,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.flush()
        return EvaluationPassRecord(
            id=row.id,
            tenant_id=row.tenant_id,
            run_id=row.run_id,
            scope=row.scope,
            pass_index=row.pass_index,
            status=row.status,
        )

    async def persist_section_results(
        self,
        *,
        evaluation_pass: EvaluationPassRecord,
        section_results: tuple[SectionEvaluationResult, ...],
    ) -> None:
        now = datetime.now(tz=UTC)
        ordered_results = sorted(
            section_results,
            key=lambda item: (item.section_order, item.section_id),
        )
        for result in ordered_results:
            section_result_id = add_section_result_row(
                self._session,
                evaluation_pass=evaluation_pass,
                result=result,
                now=now,
            )
            claim_ids = add_claim_rows(
                self._session,
                evaluation_pass=evaluation_pass,
                result=result,
                now=now,
            )
            await self._session.flush()
            add_issue_rows(
                self._session,
                evaluation_pass=evaluation_pass,
                result=result,
                section_result_id=section_result_id,
                claim_ids=claim_ids,
                now=now,
            )
        await self._session.flush()

    async def finalize_pass(
        self,
        *,
        evaluation_pass: EvaluationPassRecord,
        summary: EvaluationSummary,
    ) -> None:
        row = await self._session.scalar(
            select(EvaluationPassRow).where(EvaluationPassRow.id == evaluation_pass.id)
        )
        if row is None:
            return
        now = datetime.now(tz=UTC)
        row.status = "completed"
        row.section_count = summary.section_count
        row.evaluated_section_count = summary.evaluated_section_count
        row.issue_count = summary.issue_count
        row.sections_requiring_repair_count = summary.sections_requiring_repair_count
        row.quality_pct = summary.quality_pct
        row.unsupported_claim_rate = summary.unsupported_claim_rate
        row.pass_rate = summary.pass_rate
        row.ragas_faithfulness_pct = summary.ragas_faithfulness_pct
        row.issues_by_type_json = summary.issues_by_type
        row.completed_at = now
        row.updated_at = now
        await self._session.flush()

    async def latest_summary(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
    ) -> EvaluationSummary | None:
        row = await self._session.scalar(
            select(EvaluationPassRow)
            .where(
                EvaluationPassRow.tenant_id == tenant_id,
                EvaluationPassRow.run_id == run_id,
                EvaluationPassRow.status == "completed",
            )
            .order_by(EvaluationPassRow.pass_index.desc())
            .limit(1)
        )
        if row is None:
            return None
        repair_rows = (
            await self._session.scalars(
                select(EvaluationSectionResultRow)
                .where(
                    EvaluationSectionResultRow.tenant_id == tenant_id,
                    EvaluationSectionResultRow.evaluation_pass_id == row.id,
                    EvaluationSectionResultRow.repair_recommended.is_(True),
                )
                .order_by(
                    EvaluationSectionResultRow.section_order.asc(),
                    EvaluationSectionResultRow.section_id.asc(),
                )
            )
        ).all()
        return EvaluationSummary(
            evaluation_pass_id=row.id,
            section_count=row.section_count,
            evaluated_section_count=row.evaluated_section_count,
            issue_count=row.issue_count,
            sections_requiring_repair_count=row.sections_requiring_repair_count,
            quality_pct=row.quality_pct,
            unsupported_claim_rate=row.unsupported_claim_rate,
            pass_rate=row.pass_rate,
            ragas_faithfulness_pct=row.ragas_faithfulness_pct,
            issues_by_type=row.issues_by_type_json,
            repair_recommended=bool(row.sections_requiring_repair_count),
            sections_requiring_repair=tuple(item.section_id for item in repair_rows),
        )

    async def list_issues(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
        section_id: str | None = None,
    ) -> tuple[EvaluationIssuePayload, ...]:
        query = (
            select(EvaluationIssueRow)
            .where(EvaluationIssueRow.tenant_id == tenant_id, EvaluationIssueRow.run_id == run_id)
            .order_by(
                EvaluationIssueRow.section_order.asc(),
                EvaluationIssueRow.section_id.asc(),
                EvaluationIssueRow.claim_index.asc(),
                EvaluationIssueRow.id.asc(),
            )
        )
        if section_id is not None:
            query = query.where(EvaluationIssueRow.section_id == section_id)
        rows = (await self._session.scalars(query)).all()
        return tuple(issue_payload(row) for row in rows)

    async def load_repair_candidates(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
    ) -> tuple[RepairCandidatePayload, ...]:
        latest = await latest_completed_pass(self._session, tenant_id=tenant_id, run_id=run_id)
        if latest is None:
            return ()
        sections = (
            await self._session.scalars(
                select(EvaluationSectionResultRow)
                .where(
                    EvaluationSectionResultRow.tenant_id == tenant_id,
                    EvaluationSectionResultRow.evaluation_pass_id == latest.id,
                )
                .order_by(
                    EvaluationSectionResultRow.section_order.asc(),
                    EvaluationSectionResultRow.section_id.asc(),
                )
            )
        ).all()
        issues = await self.list_issues(tenant_id=tenant_id, run_id=run_id)
        grouped: dict[str, list[EvaluationIssuePayload]] = defaultdict(list)
        for issue in issues:
            grouped[issue.section_id].append(issue)
        return tuple(
            RepairCandidatePayload(
                section_id=section.section_id,
                ragas_faithfulness_pct=section.ragas_faithfulness_pct,
                section_has_contradicted_claim=section.section_has_contradicted_claim,
                repair_recommended=section.repair_recommended,
                max_repairs_per_section=MAX_REPAIRS_PER_SECTION,
                issue_ids=tuple(issue.issue_id for issue in grouped[section.section_id]),
                allowed_chunk_ids=(
                    grouped[section.section_id][0].allowed_chunk_ids
                    if grouped[section.section_id]
                    else ()
                ),
            )
            for section in sections
        )
