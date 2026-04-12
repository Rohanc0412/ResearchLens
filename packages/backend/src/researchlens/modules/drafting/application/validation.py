from uuid import UUID

from researchlens.modules.drafting.application.dto import SectionDraftPayload
from researchlens.modules.drafting.domain import (
    DraftingSection,
    EvidencePack,
    SectionDraft,
    ensure_only_valid_citation_tokens,
)
from researchlens.shared.errors import ValidationError


def validate_section_payload(
    *,
    payload: SectionDraftPayload,
    section: DraftingSection,
    evidence_pack: EvidencePack,
    provider_name: str,
    model_name: str,
) -> SectionDraft:
    if payload.section_id != section.section_id:
        raise ValidationError("Drafted section id did not match the requested section.")
    tokens = ensure_only_valid_citation_tokens(payload.section_text)
    if not tokens:
        raise ValidationError("Drafted section text must include at least one citation token.")
    ensure_citations_allowed(tokens=tokens, evidence_pack=evidence_pack)
    return SectionDraft(
        run_id=section.run_id,
        tenant_id=section.tenant_id,
        section=section,
        section_text=payload.section_text,
        section_summary=payload.section_summary,
        status=payload.status,
        provider_name=provider_name,
        model_name=model_name,
    )


def ensure_citations_allowed(*, tokens: tuple[UUID, ...], evidence_pack: EvidencePack) -> None:
    allowed = evidence_pack.allowed_chunk_ids
    if any(token not in allowed for token in tokens):
        raise ValidationError("Drafted section referenced evidence outside the allowed pack.")
