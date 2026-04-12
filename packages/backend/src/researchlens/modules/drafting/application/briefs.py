from uuid import UUID

from researchlens.modules.drafting.domain import (
    AllowedEvidenceItem,
    DraftingSection,
    EvidencePack,
    SectionBrief,
)


def build_evidence_summary(pack: EvidencePack) -> str:
    lines = []
    for index, item in enumerate(pack.items, start=1):
        lines.append(f"{index}. {item.title} | chunk={item.chunk_id} | excerpt={item.text_excerpt}")
    return "\n".join(lines)


def build_section_brief(
    *,
    report_title: str,
    section: DraftingSection,
    evidence_pack: EvidencePack,
    prior_continuity_summary: str | None,
) -> SectionBrief:
    return SectionBrief(
        report_title=report_title,
        section=section,
        evidence_pack=evidence_pack,
        evidence_summary=build_evidence_summary(evidence_pack),
        prior_continuity_summary=prior_continuity_summary,
    )


def to_allowed_evidence_item(
    *,
    tenant_id: UUID,
    run_id: UUID,
    source_id: UUID,
    chunk_id: UUID,
    source_rank: int,
    chunk_index: int,
    title: str,
    excerpt: str,
) -> AllowedEvidenceItem:
    return AllowedEvidenceItem(
        tenant_id=tenant_id,
        run_id=run_id,
        source_id=source_id,
        chunk_id=chunk_id,
        source_rank=source_rank,
        chunk_index=chunk_index,
        title=title,
        text_excerpt=excerpt,
    )
