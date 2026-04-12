from uuid import UUID

from researchlens.modules.evaluation.application.dtos import EvaluationIssuePayload
from researchlens.modules.evaluation.domain import (
    ClaimVerdict,
    EvaluationIssueSeverity,
    EvaluationIssueType,
)
from researchlens.modules.evaluation.infrastructure.rows import EvaluationIssueRow


def issue_payload(row: EvaluationIssueRow) -> EvaluationIssuePayload:
    return EvaluationIssuePayload(
        issue_id=row.id,
        run_id=row.run_id,
        evaluation_pass_id=row.evaluation_pass_id,
        section_id=row.section_id,
        section_title=row.section_title,
        section_order=row.section_order,
        claim_id=row.claim_id,
        claim_index=row.claim_index,
        claim_text=row.claim_text,
        verdict=ClaimVerdict(row.verdict) if row.verdict else None,
        issue_type=EvaluationIssueType(row.issue_type),
        severity=EvaluationIssueSeverity(row.severity),
        message=row.message,
        rationale=row.rationale,
        cited_chunk_ids=tuple(UUID(item) for item in row.cited_chunk_ids_json),
        supported_chunk_ids=tuple(UUID(item) for item in row.supported_chunk_ids_json),
        allowed_chunk_ids=tuple(UUID(item) for item in row.allowed_chunk_ids_json),
        repair_hint=row.repair_hint,
        created_at=row.created_at,
    )
