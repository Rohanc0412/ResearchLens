from uuid import uuid4

import pytest
from pydantic import ValidationError as PydanticValidationError

from researchlens.modules.drafting.application.assembly import assemble_report
from researchlens.modules.drafting.application.briefs import build_section_brief
from researchlens.modules.drafting.application.dto import SectionDraftPayload
from researchlens.modules.drafting.application.prompts import render_section_prompt
from researchlens.modules.drafting.domain import (
    AllowedEvidenceItem,
    DraftingSection,
    EvidencePack,
    SectionDraft,
    normalize_citation_tokens,
    parse_citation_tokens,
)
from researchlens.shared.errors import ValidationError


def test_evidence_pack_orders_items_and_enforces_run_scope() -> None:
    tenant_id = uuid4()
    run_id = uuid4()
    pack = EvidencePack(
        tenant_id=tenant_id,
        run_id=run_id,
        section_id="overview",
        items=(
            AllowedEvidenceItem(
                tenant_id=tenant_id,
                run_id=run_id,
                chunk_id=uuid4(),
                source_id=uuid4(),
                source_rank=2,
                chunk_index=1,
                title="Later",
                text_excerpt="Later excerpt",
            ),
            AllowedEvidenceItem(
                tenant_id=tenant_id,
                run_id=run_id,
                chunk_id=uuid4(),
                source_id=uuid4(),
                source_rank=1,
                chunk_index=0,
                title="Earlier",
                text_excerpt="Earlier excerpt",
            ),
        ),
    )

    assert [item.source_rank for item in pack.items] == [1, 2]


def test_evidence_pack_rejects_empty_items() -> None:
    with pytest.raises(ValidationError):
        EvidencePack(
            tenant_id=uuid4(),
            run_id=uuid4(),
            section_id="overview",
            items=(),
        )


def test_prompt_rendering_contains_allowed_evidence_and_boundaries() -> None:
    tenant_id = uuid4()
    run_id = uuid4()
    section = DraftingSection(
        run_id=run_id,
        tenant_id=tenant_id,
        section_id="overview",
        title="Overview",
        section_order=1,
        goal="Explain the area.",
        key_points=("benchmarks",),
    )
    pack = EvidencePack(
        tenant_id=tenant_id,
        run_id=run_id,
        section_id="overview",
        items=(
            AllowedEvidenceItem(
                tenant_id=tenant_id,
                run_id=run_id,
                chunk_id=uuid4(),
                source_id=uuid4(),
                source_rank=1,
                chunk_index=0,
                title="Key source",
                text_excerpt="Evidence excerpt",
            ),
        ),
    )
    brief = build_section_brief(
        report_title="AI safety",
        section=section,
        evidence_pack=pack,
        prior_continuity_summary=None,
    )

    prompt = render_section_prompt(brief, min_words=100, max_words=200)

    assert "Allowed evidence items" in prompt
    assert str(pack.items[0].chunk_id) in prompt
    assert "Do not include the section heading" in prompt


def test_citation_parsing_and_report_assembly_are_deterministic() -> None:
    tenant_id = uuid4()
    run_id = uuid4()
    first_id = uuid4()
    second_id = uuid4()
    first = SectionDraft(
        run_id=run_id,
        tenant_id=tenant_id,
        section=DraftingSection(
            run_id=run_id,
            tenant_id=tenant_id,
            section_id="a",
            title="A",
            section_order=2,
            goal="Goal",
            key_points=(),
        ),
        section_text=f"Later text [[chunk:{second_id}]]",
        section_summary="Later bridge",
        status="completed",
        provider_name="openai",
        model_name="gpt-5-nano",
    )
    second = SectionDraft(
        run_id=run_id,
        tenant_id=tenant_id,
        section=DraftingSection(
            run_id=run_id,
            tenant_id=tenant_id,
            section_id="b",
            title="B",
            section_order=1,
            goal="Goal",
            key_points=(),
        ),
        section_text=f"Earlier text [[chunk:{first_id}]]",
        section_summary="Earlier bridge",
        status="completed",
        provider_name="openai",
        model_name="gpt-5-nano",
    )

    report = assemble_report(
        run_id=run_id,
        tenant_id=tenant_id,
        report_title="Report",
        drafts=(first, second),
    )

    assert parse_citation_tokens(first.section_text) == (second_id,)
    assert report.markdown_text.startswith("# Report\n\n## B")


def test_section_draft_payload_is_strict() -> None:
    with pytest.raises(PydanticValidationError):
        SectionDraftPayload.model_validate(
            {
                "section_id": "overview",
                "section_text": "Text",
                "section_summary": "Bridge",
                "status": "completed",
                "extra": True,
            }
        )


def test_citation_normalization_accepts_common_model_variants() -> None:
    chunk_id = uuid4()

    normalized = normalize_citation_tokens(
        f"Evidence [Chunk: {chunk_id}] and [[ chunk : {chunk_id} ]] and [[source {chunk_id}]]"
    )

    assert normalized == (
        f"Evidence [[chunk:{str(chunk_id).lower()}]] "
        f"and [[chunk:{str(chunk_id).lower()}]] "
        f"and [[chunk:{str(chunk_id).lower()}]]"
    )
