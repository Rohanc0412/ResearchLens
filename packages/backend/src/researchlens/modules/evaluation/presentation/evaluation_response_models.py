from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EvaluationSummaryResponse(BaseModel):
    evaluation_pass_id: UUID
    section_count: int
    evaluated_section_count: int
    issue_count: int
    sections_requiring_repair_count: int
    quality_pct: float
    unsupported_claim_rate: float
    pass_rate: float
    ragas_faithfulness_pct: float
    issues_by_type: dict[str, int]
    repair_recommended: bool
    sections_requiring_repair: tuple[str, ...]

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class EvaluationIssueResponse(BaseModel):
    issue_id: UUID
    run_id: UUID
    evaluation_pass_id: UUID
    section_id: str
    section_title: str
    section_order: int
    claim_id: UUID | None
    claim_index: int | None
    claim_text: str | None
    verdict: str | None
    issue_type: str
    severity: str
    message: str
    rationale: str
    cited_chunk_ids: tuple[UUID, ...]
    supported_chunk_ids: tuple[UUID, ...]
    allowed_chunk_ids: tuple[UUID, ...]
    repair_hint: str
    created_at: datetime

    model_config = ConfigDict(extra="forbid", from_attributes=True)
