from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError as PydanticValidationError

from researchlens.modules.evaluation.application.citation_validation import invalid_citation_ids
from researchlens.modules.evaluation.application.dtos import EvaluatedClaimPayload
from researchlens.modules.evaluation.domain import (
    MAX_REPAIRS_PER_SECTION,
    ClaimVerdict,
    pass_rate,
    report_quality,
    section_quality,
    section_requires_repair,
    unsupported_claim_rate,
)


def test_scoring_policy_is_deterministic() -> None:
    verdicts = (
        ClaimVerdict.SUPPORTED,
        ClaimVerdict.MISSING_CITATION,
        ClaimVerdict.OVERSTATED,
        ClaimVerdict.UNSUPPORTED,
        ClaimVerdict.CONTRADICTED,
    )

    assert section_quality(verdicts) == 25.0
    assert unsupported_claim_rate(verdicts) == 40.0
    assert report_quality((100.0, 50.0)) == 75.0
    assert pass_rate((False, True, False, True)) == 50.0


@pytest.mark.parametrize(
    ("faithfulness", "verdicts", "expected"),
    [
        (69.99, (ClaimVerdict.SUPPORTED,), True),
        (70.0, (ClaimVerdict.CONTRADICTED,), True),
        (70.0, (ClaimVerdict.UNSUPPORTED,), False),
        (95.0, (ClaimVerdict.MISSING_CITATION, ClaimVerdict.OVERSTATED), False),
    ],
)
def test_repair_trigger_policy_is_exact(
    faithfulness: float,
    verdicts: tuple[ClaimVerdict, ...],
    expected: bool,
) -> None:
    assert (
        section_requires_repair(ragas_faithfulness_pct=faithfulness, verdicts=verdicts)
        is expected
    )
    assert MAX_REPAIRS_PER_SECTION == 1


def test_evaluated_claim_payload_is_strict() -> None:
    with pytest.raises(PydanticValidationError):
        EvaluatedClaimPayload.model_validate(
            {
                "claim_index": 1,
                "claim_text": "Claim",
                "verdict": "supported",
                "rationale": "Grounded",
                "repair_hint": "No repair",
                "unexpected": True,
            }
        )


def test_invalid_citation_ids_are_limited_to_allowed_chunk_ids() -> None:
    allowed = uuid4()
    invalid = uuid4()

    invalid_ids = invalid_citation_ids(
        cited_chunk_ids=(allowed, invalid),
        allowed_chunk_ids=(allowed,),
    )
    assert invalid_ids == (invalid,)
    assert invalid_citation_ids(cited_chunk_ids=(), allowed_chunk_ids=(UUID(int=0),)) == ()
