from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from researchlens.modules.evaluation.domain.claim_verdicts import ClaimVerdict
from researchlens.modules.evaluation.domain.issue_types import EvaluationIssueType
from researchlens.modules.evaluation.domain.severity import EvaluationIssueSeverity


@dataclass(frozen=True, slots=True)
class EvaluationClaim:
    id: UUID
    tenant_id: UUID
    evaluation_pass_id: UUID
    run_id: UUID
    section_id: str
    section_title: str
    section_order: int
    claim_index: int
    claim_text: str
    extracted_at: datetime


@dataclass(frozen=True, slots=True)
class EvaluationIssue:
    id: UUID
    tenant_id: UUID
    evaluation_pass_id: UUID
    run_id: UUID
    section_result_id: UUID
    claim_id: UUID | None
    section_id: str
    section_title: str
    section_order: int
    claim_index: int | None
    claim_text: str | None
    issue_type: EvaluationIssueType
    severity: EvaluationIssueSeverity
    verdict: ClaimVerdict | None
    message: str
    rationale: str
    cited_chunk_ids: tuple[UUID, ...]
    supported_chunk_ids: tuple[UUID, ...]
    allowed_chunk_ids: tuple[UUID, ...]
    repair_hint: str
    created_at: datetime
