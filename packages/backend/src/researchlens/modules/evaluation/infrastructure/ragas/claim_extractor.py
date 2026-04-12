from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from researchlens.modules.evaluation.application.citation_validation import invalid_citation_ids
from researchlens.modules.evaluation.application.dtos import EvaluatedClaimPayload
from researchlens.modules.evaluation.domain import ClaimVerdict
from researchlens.shared.config.evaluation import EvaluationSettings
from researchlens.shared.llm.domain import StructuredGenerationRequest
from researchlens.shared.llm.ports import StructuredGenerationClient


class ClaimOutputItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_index: int = Field(ge=1)
    claim_text: str
    verdict: ClaimVerdict
    cited_chunk_ids: list[UUID] = Field(default_factory=list)
    supported_chunk_ids: list[UUID] = Field(default_factory=list)
    rationale: str
    repair_hint: str


class ClaimOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claims: list[ClaimOutputItem] = Field(default_factory=list)


class RagasAssistedClaimExtractor:
    def __init__(
        self,
        *,
        settings: EvaluationSettings,
        generation_client: StructuredGenerationClient,
    ) -> None:
        self._settings = settings
        self._generation_client = generation_client

    async def extract_and_verify(
        self,
        *,
        section_title: str,
        section_text: str,
        allowed_chunk_ids: tuple[UUID, ...],
        evidence_context: str,
    ) -> tuple[EvaluatedClaimPayload, ...]:
        error = ""
        for attempt in range(self._settings.structured_output_retry_count + 1):
            result = await self._generation_client.generate_structured(
                StructuredGenerationRequest(
                    schema_name="evaluation_claim_verdicts",
                    system_prompt=(
                        "You extract atomic claims and evaluate only against the provided "
                        "section evidence. Return strict JSON. Use only these verdicts: "
                        "supported, missing_citation, invalid_citation, overstated, "
                        "unsupported, contradicted."
                    ),
                    prompt=_build_prompt(
                        section_title=section_title,
                        section_text=section_text,
                        allowed_chunk_ids=allowed_chunk_ids,
                        evidence_context=evidence_context,
                        max_claims=self._settings.max_claims_per_section,
                        prior_error=error,
                    ),
                    max_output_tokens=self._settings.section_max_output_tokens,
                )
            )
            try:
                parsed = ClaimOutput.model_validate(_normalize(result.data))
                return _normalize_claims(
                    claims=tuple(parsed.claims[: self._settings.max_claims_per_section]),
                    allowed_chunk_ids=allowed_chunk_ids,
                )
            except Exception as exc:
                error = str(exc)
                if attempt >= self._settings.structured_output_retry_count:
                    raise
        raise RuntimeError("Evaluation claim extraction retry loop terminated unexpectedly.")


def _build_prompt(
    *,
    section_title: str,
    section_text: str,
    allowed_chunk_ids: tuple[UUID, ...],
    evidence_context: str,
    max_claims: int,
    prior_error: str,
) -> str:
    correction = f"\nPrevious output error: {prior_error}\n" if prior_error else ""
    return (
        f"Section title: {section_title}\n"
        f"Allowed chunk ids: {[str(item) for item in allowed_chunk_ids]}\n"
        f"Max claims: {max_claims}\n"
        f"{correction}"
        "Section text:\n"
        f"{section_text}\n\n"
        "Section evidence:\n"
        f"{evidence_context}\n\n"
        "Return JSON with this shape: "
        '{"claims":[{"claim_index":1,"claim_text":"...","verdict":"supported",'
        '"cited_chunk_ids":[],"supported_chunk_ids":[],"rationale":"...",'
        '"repair_hint":"..."}]}. Keep claim_index deterministic in text order.'
    )


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    if "claims" in data:
        return data
    if "raw" in data and isinstance(data["raw"], str):
        import json

        parsed = json.loads(data["raw"])
        if isinstance(parsed, dict):
            return parsed
    return data


def _normalize_claims(
    *,
    claims: tuple[ClaimOutputItem, ...],
    allowed_chunk_ids: tuple[UUID, ...],
) -> tuple[EvaluatedClaimPayload, ...]:
    normalized: list[EvaluatedClaimPayload] = []
    seen_indexes: set[int] = set()
    allowed = frozenset(allowed_chunk_ids)
    for position, item in enumerate(claims, start=1):
        index = item.claim_index if item.claim_index not in seen_indexes else position
        seen_indexes.add(index)
        cited = tuple(item.cited_chunk_ids)
        supported = tuple(chunk_id for chunk_id in item.supported_chunk_ids if chunk_id in allowed)
        verdict = item.verdict
        if invalid_citation_ids(cited_chunk_ids=cited, allowed_chunk_ids=allowed_chunk_ids):
            verdict = ClaimVerdict.INVALID_CITATION
        elif not cited and verdict == ClaimVerdict.SUPPORTED:
            verdict = ClaimVerdict.MISSING_CITATION
        normalized.append(
            EvaluatedClaimPayload(
                claim_index=index,
                claim_text=item.claim_text,
                verdict=verdict,
                cited_chunk_ids=cited,
                supported_chunk_ids=supported,
                rationale=item.rationale,
                repair_hint=item.repair_hint,
            )
        )
    return tuple(sorted(normalized, key=lambda claim: claim.claim_index))
