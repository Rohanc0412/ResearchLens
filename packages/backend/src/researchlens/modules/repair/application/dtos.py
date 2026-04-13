from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RepairEvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    chunk_id: UUID
    source_id: UUID
    source_title: str
    source_rank: int = Field(ge=1)
    chunk_index: int = Field(ge=0)
    text: str


class RepairIssueInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    issue_id: UUID
    issue_type: str
    severity: str
    verdict: str | None = None
    rationale: str
    message: str
    claim_id: UUID | None = None
    claim_index: int | None = None
    claim_text: str | None = None
    cited_chunk_ids: tuple[UUID, ...] = ()
    supported_chunk_ids: tuple[UUID, ...] = ()
    allowed_chunk_ids: tuple[UUID, ...] = ()
    repair_hint: str


class SectionRepairInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: UUID
    run_id: UUID
    section_id: str
    section_title: str
    section_order: int = Field(ge=1)
    current_section_text: str
    current_section_summary: str
    evaluation_section_result_id: UUID
    evaluation_pass_id: UUID
    repair_attempt_count: int = Field(ge=0)
    ragas_faithfulness_pct: float = Field(ge=0, le=100)
    triggered_by_low_faithfulness: bool
    triggered_by_contradiction: bool
    issues: tuple[RepairIssueInput, ...]
    evidence: tuple[RepairEvidenceRef, ...]

    @property
    def allowed_chunk_ids(self) -> tuple[UUID, ...]:
        return tuple(item.chunk_id for item in self.evidence)


class RepairPassRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    tenant_id: UUID
    run_id: UUID
    pass_index: int = Field(ge=1)
    status: str


class RepairOutputPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    section_id: str
    revised_text: str
    revised_summary: str
    addressed_issue_ids: tuple[UUID, ...]
    citations_used: tuple[UUID, ...]
    self_check: str

    @field_validator("revised_text", "revised_summary", "self_check")
    @classmethod
    def _required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field is required.")
        return stripped


class SectionRepairOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    repair_result_id: UUID
    section_id: str
    action: str
    status: str
    changed: bool
    revised_text: str | None = None
    revised_summary: str | None = None
    unresolved_reason: str | None = None


class RepairExecutionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    repair_pass_id: UUID | None
    selected_section_ids: tuple[str, ...]
    changed_section_ids: tuple[str, ...]
    unresolved_section_ids: tuple[str, ...]
    skipped_section_ids: tuple[str, ...]
    result_ids_by_section: dict[str, UUID]


class RepairReadSection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    section_id: str
    section_title: str
    section_order: int
    status: str
    action: str
    changed: bool
    evaluation_section_result_id: UUID
    repair_result_id: UUID
    reevaluation_pass_id: UUID | None = None
    unresolved_reason: str | None = None


class RepairReadSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    repair_pass_id: UUID | None
    run_id: UUID
    status: str
    selected_count: int
    changed_count: int
    unresolved_count: int
    sections: tuple[RepairReadSection, ...]
