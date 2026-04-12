from uuid import uuid4

import pytest

from researchlens.modules.evaluation.domain import ClaimVerdict
from researchlens.modules.evaluation.infrastructure.ragas.claim_extractor import (
    RagasAssistedClaimExtractor,
)
from researchlens.shared.config.evaluation import EvaluationSettings
from researchlens.shared.llm.domain import StructuredGenerationRequest, StructuredGenerationResult


class _ClaimClient:
    def __init__(self, *, allowed: object, invalid: object) -> None:
        self.allowed = allowed
        self.invalid = invalid

    @property
    def model(self) -> str:
        return "gpt-5-nano"

    async def generate_structured(
        self,
        request: StructuredGenerationRequest,
    ) -> StructuredGenerationResult:
        assert request.schema_name == "evaluation_claim_verdicts"
        return StructuredGenerationResult(
            data={
                "claims": [
                    {
                        "claim_index": 1,
                        "claim_text": "Allowed claim",
                        "verdict": "supported",
                        "cited_chunk_ids": [str(self.allowed)],
                        "supported_chunk_ids": [str(self.allowed)],
                        "rationale": "Allowed evidence supports it.",
                        "repair_hint": "No repair.",
                    },
                    {
                        "claim_index": 2,
                        "claim_text": "Invalid citation claim",
                        "verdict": "supported",
                        "cited_chunk_ids": [str(self.invalid)],
                        "supported_chunk_ids": [str(self.invalid)],
                        "rationale": "Citation is outside the pack.",
                        "repair_hint": "Use allowed evidence only.",
                    },
                ]
            }
        )


@pytest.mark.asyncio
async def test_claim_extractor_normalizes_invalid_citations() -> None:
    allowed = uuid4()
    invalid = uuid4()
    client = _ClaimClient(allowed=allowed, invalid=invalid)
    extractor = RagasAssistedClaimExtractor(
        settings=EvaluationSettings(),
        generation_client=client,
    )

    claims = await extractor.extract_and_verify(
        section_title="Overview",
        section_text=f"Allowed [[chunk:{allowed}]] invalid [[chunk:{invalid}]]",
        allowed_chunk_ids=(allowed,),
        evidence_context="Allowed evidence",
    )

    assert claims[0].verdict == ClaimVerdict.SUPPORTED
    assert claims[1].verdict == ClaimVerdict.INVALID_CITATION
    assert claims[1].supported_chunk_ids == ()
