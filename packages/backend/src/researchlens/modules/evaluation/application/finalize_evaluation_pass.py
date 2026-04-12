from collections import Counter
from uuid import UUID

from researchlens.modules.evaluation.application.dtos import (
    EvaluationSummary,
    SectionEvaluationResult,
)
from researchlens.modules.evaluation.domain import pass_rate, report_quality


def summarize_results(
    *,
    evaluation_pass_id: UUID,
    section_count: int,
    section_results: tuple[SectionEvaluationResult, ...],
) -> EvaluationSummary:
    repair_sections = tuple(
        result.section_id for result in section_results if result.repair_recommended
    )
    issue_counts = Counter(
        issue.issue_type.value for result in section_results for issue in result.issues
    )
    claim_rates = [result.unsupported_claim_rate for result in section_results]
    faithfulness = [result.ragas_faithfulness_pct for result in section_results]
    unsupported_rate = round(sum(claim_rates) / len(claim_rates), 2) if claim_rates else 0.0
    return EvaluationSummary(
        evaluation_pass_id=evaluation_pass_id,
        section_count=section_count,
        evaluated_section_count=len(section_results),
        issue_count=sum(issue_counts.values()),
        sections_requiring_repair_count=len(repair_sections),
        quality_pct=report_quality(tuple(result.quality_score for result in section_results)),
        unsupported_claim_rate=unsupported_rate,
        pass_rate=pass_rate(tuple(result.repair_recommended for result in section_results)),
        ragas_faithfulness_pct=(
            round(sum(faithfulness) / len(faithfulness), 2) if faithfulness else 0.0
        ),
        issues_by_type=dict(sorted(issue_counts.items())),
        repair_recommended=bool(repair_sections),
        sections_requiring_repair=repair_sections,
    )
