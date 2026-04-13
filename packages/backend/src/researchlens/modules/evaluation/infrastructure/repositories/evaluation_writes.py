from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.evaluation.application.dtos import (
    EvaluationPassRecord,
    SectionEvaluationResult,
)
from researchlens.modules.evaluation.infrastructure.rows import (
    EvaluationClaimRow,
    EvaluationIssueRow,
    EvaluationSectionResultRow,
)


def add_section_result_row(
    session: AsyncSession,
    *,
    evaluation_pass: EvaluationPassRecord,
    result: SectionEvaluationResult,
    now: datetime,
) -> UUID:
    section_result_id = uuid4()
    session.add(
        EvaluationSectionResultRow(
            id=section_result_id,
            tenant_id=evaluation_pass.tenant_id,
            evaluation_pass_id=evaluation_pass.id,
            run_id=evaluation_pass.run_id,
            section_id=result.section_id,
            section_title=result.section_title,
            section_order=result.section_order,
            quality_score=result.quality_score,
            claim_count=len(result.claims),
            issue_count=len(result.issues),
            unsupported_claim_rate=result.unsupported_claim_rate,
            ragas_faithfulness_pct=result.ragas_faithfulness_pct,
            section_has_contradicted_claim=result.section_has_contradicted_claim,
            repair_recommended=result.repair_recommended,
            repair_attempt_count=0,
            repair_result_id=result.repair_result_id,
            created_at=now,
            updated_at=now,
        )
    )
    return section_result_id


def add_claim_rows(
    session: AsyncSession,
    *,
    evaluation_pass: EvaluationPassRecord,
    result: SectionEvaluationResult,
    now: datetime,
) -> dict[int, UUID]:
    claim_ids: dict[int, UUID] = {}
    for claim in sorted(result.claims, key=lambda item: item.claim_index):
        claim_id = uuid4()
        claim_ids[claim.claim_index] = claim_id
        session.add(
            EvaluationClaimRow(
                id=claim_id,
                tenant_id=evaluation_pass.tenant_id,
                evaluation_pass_id=evaluation_pass.id,
                run_id=evaluation_pass.run_id,
                section_id=result.section_id,
                section_title=result.section_title,
                section_order=result.section_order,
                claim_index=claim.claim_index,
                claim_text=claim.claim_text,
                extracted_at=now,
            )
        )
    return claim_ids


def add_issue_rows(
    session: AsyncSession,
    *,
    evaluation_pass: EvaluationPassRecord,
    result: SectionEvaluationResult,
    section_result_id: UUID,
    claim_ids: dict[int, UUID],
    now: datetime,
) -> None:
    for issue in sorted(
        result.issues,
        key=lambda item: (item.section_order, item.section_id, item.claim_index or 0),
    ):
        session.add(
            EvaluationIssueRow(
                id=issue.issue_id,
                tenant_id=evaluation_pass.tenant_id,
                evaluation_pass_id=evaluation_pass.id,
                run_id=evaluation_pass.run_id,
                section_result_id=section_result_id,
                claim_id=claim_ids.get(issue.claim_index or 0),
                section_id=issue.section_id,
                section_title=issue.section_title,
                section_order=issue.section_order,
                claim_index=issue.claim_index,
                claim_text=issue.claim_text,
                issue_type=issue.issue_type.value,
                severity=issue.severity.value,
                verdict=issue.verdict.value if issue.verdict else None,
                message=issue.message,
                rationale=issue.rationale,
                cited_chunk_ids_json=[str(item) for item in issue.cited_chunk_ids],
                supported_chunk_ids_json=[str(item) for item in issue.supported_chunk_ids],
                allowed_chunk_ids_json=[str(item) for item in issue.allowed_chunk_ids],
                repair_hint=issue.repair_hint,
                created_at=now,
            )
        )
