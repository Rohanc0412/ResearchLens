from uuid import UUID

from researchlens.modules.evaluation.application.dtos import (
    EvaluationRunInput,
    EvaluationSectionInput,
    SectionEvaluationResult,
)
from researchlens.modules.evaluation.infrastructure.ragas.claim_extractor import (
    RagasAssistedClaimExtractor,
)
from researchlens.modules.evaluation.infrastructure.ragas.faithfulness_scorer import (
    RagasFaithfulnessScorer,
)


class RagasGroundingEvaluator:
    def __init__(
        self,
        *,
        claim_extractor: RagasAssistedClaimExtractor,
        faithfulness_scorer: RagasFaithfulnessScorer,
    ) -> None:
        self._claim_extractor = claim_extractor
        self._faithfulness_scorer = faithfulness_scorer

    async def evaluate_section(
        self,
        *,
        evaluation_pass_id: UUID,
        run_input: EvaluationRunInput,
        section: EvaluationSectionInput,
    ) -> SectionEvaluationResult:
        evidence_contexts = tuple(
            f"chunk_id={item.chunk_id}\ntitle={item.source_title}\ntext={item.text}"
            for item in section.allowed_evidence
        )
        evidence_context = "\n\n".join(evidence_contexts)
        claims = await self._claim_extractor.extract_and_verify(
            section_title=section.section_title,
            section_text=section.section_text,
            allowed_chunk_ids=section.allowed_chunk_ids,
            evidence_context=evidence_context,
        )
        faithfulness_pct = await self._faithfulness_scorer.score(
            user_input=run_input.research_question,
            response=section.section_text,
            retrieved_contexts=evidence_contexts,
        )
        return SectionEvaluationResult(
            section_id=section.section_id,
            section_title=section.section_title,
            section_order=section.section_order,
            claims=claims,
            issues=(),
            quality_score=0.0,
            unsupported_claim_rate=0.0,
            ragas_faithfulness_pct=faithfulness_pct,
            section_has_contradicted_claim=False,
            repair_recommended=False,
        )
