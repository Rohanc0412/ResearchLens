from researchlens.modules.drafting.domain import SectionBrief
from researchlens.shared.llm.domain import StructuredGenerationRequest


def render_section_prompt(brief: SectionBrief, *, min_words: int, max_words: int) -> str:
    continuity = brief.prior_continuity_summary or "None"
    key_points = ", ".join(brief.section.key_points) if brief.section.key_points else "None"
    return (
        f"Report title: {brief.report_title}\n"
        f"Section id: {brief.section.section_id}\n"
        f"Section title: {brief.section.title}\n"
        f"Section order: {brief.section.section_order}\n"
        f"Section goal: {brief.section.goal}\n"
        f"Key points: {key_points}\n"
        f"Previous continuity summary: {continuity}\n"
        f"Allowed evidence items:\n{brief.evidence_summary}\n\n"
        "Write markdown body text only. Do not include the section heading.\n"
        f"Target length: {min_words}-{max_words} words.\n"
        "Support factual claims with citation tokens in the exact format "
        "[[chunk:<uuid>]] using only the allowed chunk ids above.\n"
        "A short transition sentence may be uncited only if it introduces no new facts.\n"
        "Return strict JSON with: section_id, section_text, section_summary, status.\n"
        "section_summary must be a short continuity-only bridge with no citations and no new facts."
    )


def build_section_request(
    brief: SectionBrief,
    *,
    min_words: int,
    max_words: int,
    max_output_tokens: int,
) -> StructuredGenerationRequest:
    return StructuredGenerationRequest(
        schema_name="drafting_section",
        system_prompt=(
            "You are drafting a grounded research report section. "
            "Use only the allowed evidence. Never invent citations."
        ),
        prompt=render_section_prompt(
            brief,
            min_words=min_words,
            max_words=max_words,
        ),
        max_output_tokens=max_output_tokens,
    )
