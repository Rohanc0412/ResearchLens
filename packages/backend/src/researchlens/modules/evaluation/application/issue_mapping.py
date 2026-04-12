from datetime import UTC, datetime
from uuid import UUID, uuid4

from researchlens.modules.evaluation.application.dtos import (
    EvaluatedClaimPayload,
    EvaluationIssuePayload,
    EvaluationSectionInput,
)
from researchlens.modules.evaluation.domain import ClaimVerdict
from researchlens.modules.evaluation.domain.issue_types import EvaluationIssueType
from researchlens.modules.evaluation.domain.severity import EvaluationIssueSeverity


def issue_for_claim(
    *,
    run_id: UUID,
    evaluation_pass_id: UUID,
    section: EvaluationSectionInput,
    claim: EvaluatedClaimPayload,
    claim_id: UUID | None,
) -> EvaluationIssuePayload | None:
    issue_type = _issue_type_for_verdict(claim.verdict)
    if issue_type is None:
        return None
    return EvaluationIssuePayload(
        issue_id=uuid4(),
        run_id=run_id,
        evaluation_pass_id=evaluation_pass_id,
        section_id=section.section_id,
        section_title=section.section_title,
        section_order=section.section_order,
        claim_id=claim_id,
        claim_index=claim.claim_index,
        claim_text=claim.claim_text,
        verdict=claim.verdict,
        issue_type=issue_type,
        severity=(
            EvaluationIssueSeverity.ERROR
            if claim.verdict in {ClaimVerdict.UNSUPPORTED, ClaimVerdict.CONTRADICTED}
            else EvaluationIssueSeverity.WARNING
        ),
        message=_message_for_verdict(claim.verdict),
        rationale=claim.rationale,
        cited_chunk_ids=claim.cited_chunk_ids,
        supported_chunk_ids=claim.supported_chunk_ids,
        allowed_chunk_ids=section.allowed_chunk_ids,
        repair_hint=claim.repair_hint,
        created_at=datetime.now(tz=UTC),
    )


def section_issue(
    *,
    run_id: UUID,
    evaluation_pass_id: UUID,
    section: EvaluationSectionInput,
    issue_type: EvaluationIssueType,
    message: str,
) -> EvaluationIssuePayload:
    return EvaluationIssuePayload(
        issue_id=uuid4(),
        run_id=run_id,
        evaluation_pass_id=evaluation_pass_id,
        section_id=section.section_id,
        section_title=section.section_title,
        section_order=section.section_order,
        issue_type=issue_type,
        severity=EvaluationIssueSeverity.ERROR,
        message=message,
        rationale=message,
        allowed_chunk_ids=section.allowed_chunk_ids,
        repair_hint=message,
        created_at=datetime.now(tz=UTC),
    )


def _issue_type_for_verdict(verdict: ClaimVerdict) -> EvaluationIssueType | None:
    if verdict == ClaimVerdict.SUPPORTED:
        return None
    return {
        ClaimVerdict.MISSING_CITATION: EvaluationIssueType.MISSING_CITATION,
        ClaimVerdict.INVALID_CITATION: EvaluationIssueType.INVALID_CITATION,
        ClaimVerdict.OVERSTATED: EvaluationIssueType.OVERSTATED_CLAIM,
        ClaimVerdict.UNSUPPORTED: EvaluationIssueType.UNSUPPORTED_CLAIM,
        ClaimVerdict.CONTRADICTED: EvaluationIssueType.CONTRADICTED_CLAIM,
    }[verdict]


def _message_for_verdict(verdict: ClaimVerdict) -> str:
    return {
        ClaimVerdict.MISSING_CITATION: "Claim is missing a citation.",
        ClaimVerdict.INVALID_CITATION: "Claim cites evidence outside the section evidence pack.",
        ClaimVerdict.OVERSTATED: "Claim overstates the cited evidence.",
        ClaimVerdict.UNSUPPORTED: "Claim is not supported by the section evidence pack.",
        ClaimVerdict.CONTRADICTED: "Claim is contradicted by the section evidence pack.",
    }.get(verdict, "Claim is supported.")
