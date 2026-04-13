from researchlens.modules.repair.application.dtos import RepairIssueInput, SectionRepairInput
from researchlens.shared.llm.domain import StructuredGenerationRequest


def build_repair_request(
    repair_input: SectionRepairInput,
    *,
    max_output_tokens: int,
) -> StructuredGenerationRequest:
    return StructuredGenerationRequest(
        schema_name="repair_section",
        system_prompt=(
            "You repair grounded research report sections. Use only the allowed evidence. "
            "Return strict JSON and do not invent citations."
        ),
        prompt=render_repair_prompt(repair_input),
        max_output_tokens=max_output_tokens,
    )


def render_repair_prompt(repair_input: SectionRepairInput) -> str:
    issues = "\n".join(_issue_line(issue) for issue in repair_input.issues)
    evidence = "\n".join(
        (
            f"- chunk={item.chunk_id} source={item.source_title} "
            f"rank={item.source_rank} index={item.chunk_index}: {item.text}"
        )
        for item in repair_input.evidence
    )
    return (
        f"Section id: {repair_input.section_id}\n"
        f"Section title: {repair_input.section_title}\n"
        f"Section order: {repair_input.section_order}\n"
        f"Faithfulness: {repair_input.ragas_faithfulness_pct}\n"
        f"Triggered by low faithfulness: {repair_input.triggered_by_low_faithfulness}\n"
        f"Triggered by contradiction: {repair_input.triggered_by_contradiction}\n"
        f"Current summary: {repair_input.current_section_summary}\n"
        f"Current text:\n{repair_input.current_section_text}\n\n"
        f"Allowed evidence:\n{evidence}\n\n"
        f"Persisted evaluation issues:\n{issues}\n\n"
        "Revise only the minimum text needed to address these issues. Preserve supported content "
        "and the section's style. Cite only allowed chunk ids using [[chunk:<uuid>]]. "
        "Return JSON with section_id, revised_text, revised_summary, addressed_issue_ids, "
        "citations_used, and self_check."
    )


def _issue_line(issue: RepairIssueInput) -> str:
    return (
        f"- issue_id={issue.issue_id} type={issue.issue_type} severity={issue.severity} "
        f"verdict={issue.verdict} claim_id={issue.claim_id} claim_index={issue.claim_index} "
        f"claim_text={issue.claim_text!r} cited={list(issue.cited_chunk_ids)} "
        f"supported={list(issue.supported_chunk_ids)} rationale={issue.rationale!r} "
        f"hint={issue.repair_hint!r}"
    )
