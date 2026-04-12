from uuid import UUID

from researchlens.modules.drafting.domain import ReportDraft, SectionDraft


def assemble_report(
    *,
    run_id: UUID,
    tenant_id: UUID,
    report_title: str,
    drafts: tuple[SectionDraft, ...],
) -> ReportDraft:
    ordered = tuple(sorted(drafts, key=lambda item: item.section.section_order))
    parts = [f"# {report_title}"]
    for draft in ordered:
        parts.append(f"## {draft.section.title}")
        parts.append(draft.section_text)
    return ReportDraft(
        run_id=run_id,
        tenant_id=tenant_id,
        title=report_title,
        markdown_text="\n\n".join(parts),
    )
