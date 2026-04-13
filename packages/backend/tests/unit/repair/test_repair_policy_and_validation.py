from uuid import uuid4

import pytest

from researchlens.modules.repair.application.dtos import (
    RepairEvidenceRef,
    RepairIssueInput,
    SectionRepairInput,
)
from researchlens.modules.repair.application.fallback_edits import try_validated_fallback
from researchlens.modules.repair.application.output_validation import parse_repair_output
from researchlens.modules.repair.application.prompting import render_repair_prompt
from researchlens.modules.repair.domain import section_is_repair_eligible, select_repair_inputs
from researchlens.shared.errors import ValidationError


def test_repair_selection_policy_is_exact_and_ordered() -> None:
    eligible_low = _repair_input(section_id="b", section_order=2, faithfulness=69.9)
    eligible_contradicted = _repair_input(
        section_id="a",
        section_order=1,
        faithfulness=95.0,
        verdict="contradicted",
    )
    not_eligible = _repair_input(section_id="c", section_order=3, faithfulness=70.0)
    exhausted = _repair_input(
        section_id="d",
        section_order=4,
        faithfulness=10.0,
        repair_attempt_count=1,
    )

    assert section_is_repair_eligible(eligible_low) is True
    assert section_is_repair_eligible(eligible_contradicted) is True
    assert section_is_repair_eligible(not_eligible) is False
    assert section_is_repair_eligible(exhausted) is False
    assert select_repair_inputs((eligible_low, not_eligible, eligible_contradicted, exhausted)) == (
        eligible_contradicted,
        eligible_low,
    )


def test_prompt_includes_persisted_issue_and_allowed_evidence_details() -> None:
    repair_input = _repair_input(section_id="methods", verdict="contradicted")

    prompt = render_repair_prompt(repair_input)

    assert str(repair_input.issues[0].issue_id) in prompt
    assert "contradicted" in prompt
    assert str(repair_input.allowed_chunk_ids[0]) in prompt
    assert "Current text:" in prompt


def test_repair_output_rejects_wrong_section_and_disallowed_citation() -> None:
    repair_input = _repair_input(section_id="results")

    with pytest.raises(ValidationError):
        parse_repair_output(
            data={
                "section_id": "other",
                "revised_text": f"Text [[chunk:{repair_input.allowed_chunk_ids[0]}]]",
                "revised_summary": "Summary",
                "addressed_issue_ids": [repair_input.issues[0].issue_id],
                "citations_used": [repair_input.allowed_chunk_ids[0]],
                "self_check": "ok",
            },
            repair_input=repair_input,
        )

    with pytest.raises(ValidationError):
        parse_repair_output(
            data={
                "section_id": "results",
                "revised_text": f"Text [[chunk:{uuid4()}]]",
                "revised_summary": "Summary",
                "addressed_issue_ids": [repair_input.issues[0].issue_id],
                "citations_used": [repair_input.allowed_chunk_ids[0]],
                "self_check": "ok",
            },
            repair_input=repair_input,
        )


def test_fallback_is_precise_or_unresolved_for_ambiguous_targets() -> None:
    precise = _repair_input(
        section_text="This section is safe. Remove this false claim. Keep this.",
        claim_text="Remove this false claim",
        verdict="contradicted",
    )
    ambiguous = _repair_input(
        section_text="Repeated false claim. Repeated false claim.",
        claim_text="Repeated false claim",
        verdict="contradicted",
    )

    assert try_validated_fallback(precise) == ("This section is safe. Keep this.", "Summary")
    assert try_validated_fallback(ambiguous) is None


def _repair_input(
    *,
    section_id: str = "overview",
    section_order: int = 1,
    faithfulness: float = 95.0,
    verdict: str | None = None,
    repair_attempt_count: int = 0,
    section_text: str | None = None,
    claim_text: str = "Problem claim",
) -> SectionRepairInput:
    tenant_id = uuid4()
    run_id = uuid4()
    chunk_id = uuid4()
    return SectionRepairInput(
        tenant_id=tenant_id,
        run_id=run_id,
        section_id=section_id,
        section_title=section_id.title(),
        section_order=section_order,
        current_section_text=section_text or f"Problem claim [[chunk:{chunk_id}]].",
        current_section_summary="Summary",
        evaluation_section_result_id=uuid4(),
        evaluation_pass_id=uuid4(),
        repair_attempt_count=repair_attempt_count,
        ragas_faithfulness_pct=faithfulness,
        triggered_by_low_faithfulness=faithfulness < 70.0,
        triggered_by_contradiction=verdict == "contradicted",
        issues=(
            RepairIssueInput(
                issue_id=uuid4(),
                issue_type="claim_contradicted",
                severity="high",
                verdict=verdict,
                rationale="Persisted evaluator rationale",
                message="Issue message",
                claim_id=uuid4(),
                claim_index=1,
                claim_text=claim_text,
                cited_chunk_ids=(chunk_id,),
                supported_chunk_ids=(),
                allowed_chunk_ids=(chunk_id,),
                repair_hint="Remove the precise unsupported claim.",
            ),
        ),
        evidence=(
            RepairEvidenceRef(
                chunk_id=chunk_id,
                source_id=uuid4(),
                source_title="Source",
                source_rank=1,
                chunk_index=0,
                text="Evidence",
            ),
        ),
    )
