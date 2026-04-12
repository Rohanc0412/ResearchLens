from uuid import UUID

from researchlens.modules.evaluation.application.dtos import (
    EvaluationRunInput,
    EvaluationSectionInput,
    SectionEvaluationResult,
)
from researchlens.modules.evaluation.application.issue_mapping import issue_for_claim, section_issue
from researchlens.modules.evaluation.application.ports import SectionGroundingEvaluator
from researchlens.modules.evaluation.domain import (
    ClaimVerdict,
    section_quality,
    section_requires_repair,
    unsupported_claim_rate,
)
from researchlens.modules.evaluation.domain.issue_types import EvaluationIssueType


async def evaluate_section(
    *,
    evaluation_pass_id: UUID,
    evaluator: SectionGroundingEvaluator,
    run_input: EvaluationRunInput,
    section: EvaluationSectionInput,
) -> SectionEvaluationResult:
    if not section.section_text.strip():
        return _section_input_issue_result(
            run_input=run_input,
            evaluation_pass_id=evaluation_pass_id,
            section=section,
            issue_type=EvaluationIssueType.EMPTY_SECTION_TEXT,
            message="Section draft text is empty.",
        )
    if not section.allowed_evidence:
        return _section_input_issue_result(
            run_input=run_input,
            evaluation_pass_id=evaluation_pass_id,
            section=section,
            issue_type=EvaluationIssueType.EMPTY_SECTION_EVIDENCE,
            message="Section evidence pack is empty.",
        )
    result = await evaluator.evaluate_section(
        evaluation_pass_id=evaluation_pass_id,
        run_input=run_input,
        section=section,
    )
    verdicts = tuple(claim.verdict for claim in result.claims)
    ordered_issues = tuple(
        issue
        for issue in (
            issue_for_claim(
                run_id=run_input.run_id,
                evaluation_pass_id=evaluation_pass_id,
                section=section,
                claim=claim,
                claim_id=None,
            )
            for claim in result.claims
        )
        if issue is not None
    )
    return result.model_copy(
        update={
            "issues": tuple((*result.issues, *ordered_issues)),
            "quality_score": section_quality(verdicts),
            "unsupported_claim_rate": unsupported_claim_rate(verdicts),
            "section_has_contradicted_claim": ClaimVerdict.CONTRADICTED in verdicts,
            "repair_recommended": section_requires_repair(
                ragas_faithfulness_pct=result.ragas_faithfulness_pct,
                verdicts=verdicts,
            ),
        }
    )


def _section_input_issue_result(
    *,
    run_input: EvaluationRunInput,
    evaluation_pass_id: UUID,
    section: EvaluationSectionInput,
    issue_type: EvaluationIssueType,
    message: str,
) -> SectionEvaluationResult:
    issue = section_issue(
        run_id=run_input.run_id,
        evaluation_pass_id=evaluation_pass_id,
        section=section,
        issue_type=issue_type,
        message=message,
    )
    return SectionEvaluationResult(
        section_id=section.section_id,
        section_title=section.section_title,
        section_order=section.section_order,
        claims=(),
        issues=(issue,),
        quality_score=0.0,
        unsupported_claim_rate=0.0,
        ragas_faithfulness_pct=0.0,
        section_has_contradicted_claim=False,
        repair_recommended=True,
    )
