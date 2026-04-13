from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from researchlens.modules.evaluation.domain import ClaimVerdict
from researchlens.modules.evaluation.domain.issue_types import EvaluationIssueType
from researchlens.modules.evaluation.domain.severity import EvaluationIssueSeverity


class EvaluationEvidenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    chunk_id: UUID
    source_id: UUID
    source_title: str
    source_rank: int = Field(ge=1)
    chunk_index: int = Field(ge=0)
    text: str


class EvaluationSectionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    section_id: str
    section_title: str
    section_order: int = Field(ge=1)
    section_text: str
    allowed_evidence: tuple[EvaluationEvidenceInput, ...]
    repair_result_id: UUID | None = None

    @property
    def allowed_chunk_ids(self) -> tuple[UUID, ...]:
        return tuple(item.chunk_id for item in self.allowed_evidence)


class EvaluationRunInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: UUID
    run_id: UUID
    research_question: str
    sections: tuple[EvaluationSectionInput, ...]


class EvaluationPassRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    tenant_id: UUID
    run_id: UUID
    scope: str
    pass_index: int = Field(ge=1)
    status: str


class EvaluatedClaimPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_index: int = Field(ge=1)
    claim_text: str
    verdict: ClaimVerdict
    cited_chunk_ids: tuple[UUID, ...] = ()
    supported_chunk_ids: tuple[UUID, ...] = ()
    rationale: str
    repair_hint: str

    @field_validator("claim_text", "rationale", "repair_hint")
    @classmethod
    def _clean_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value is required.")
        return normalized


class EvaluationIssuePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    issue_id: UUID
    run_id: UUID
    evaluation_pass_id: UUID
    section_id: str
    section_title: str
    section_order: int
    claim_id: UUID | None = None
    claim_index: int | None = None
    claim_text: str | None = None
    verdict: ClaimVerdict | None = None
    issue_type: EvaluationIssueType
    severity: EvaluationIssueSeverity
    message: str
    rationale: str
    cited_chunk_ids: tuple[UUID, ...] = ()
    supported_chunk_ids: tuple[UUID, ...] = ()
    allowed_chunk_ids: tuple[UUID, ...] = ()
    repair_hint: str
    created_at: datetime


class SectionEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    section_id: str
    section_title: str
    section_order: int
    claims: tuple[EvaluatedClaimPayload, ...]
    issues: tuple[EvaluationIssuePayload, ...]
    quality_score: float = Field(ge=0, le=100)
    unsupported_claim_rate: float = Field(ge=0, le=100)
    ragas_faithfulness_pct: float = Field(ge=0, le=100)
    section_has_contradicted_claim: bool
    repair_recommended: bool
    repair_result_id: UUID | None = None


class EvaluationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evaluation_pass_id: UUID
    section_count: int = Field(ge=0)
    evaluated_section_count: int = Field(ge=0)
    issue_count: int = Field(ge=0)
    sections_requiring_repair_count: int = Field(ge=0)
    quality_pct: float = Field(ge=0, le=100)
    unsupported_claim_rate: float = Field(ge=0, le=100)
    pass_rate: float = Field(ge=0, le=100)
    ragas_faithfulness_pct: float = Field(ge=0, le=100)
    issues_by_type: dict[str, int]
    repair_recommended: bool
    sections_requiring_repair: tuple[str, ...]


class RepairCandidatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    section_id: str
    ragas_faithfulness_pct: float
    section_has_contradicted_claim: bool
    repair_recommended: bool
    max_repairs_per_section: int
    issue_ids: tuple[UUID, ...]
    allowed_chunk_ids: tuple[UUID, ...]
