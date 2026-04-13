from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EvidenceSectionSummaryResponse(BaseModel):
    section_id: str
    title: str
    section_order: int
    repaired: bool
    issue_count: int

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class RunEvidenceSummaryResponse(BaseModel):
    run_id: UUID
    project_id: UUID
    conversation_id: UUID | None
    section_count: int
    source_count: int
    chunk_count: int
    claim_count: int
    issue_count: int
    repaired_section_count: int
    unresolved_section_count: int
    latest_evaluation_pass_id: UUID | None
    latest_repair_pass_id: UUID | None
    artifact_count: int
    sections: tuple[EvidenceSectionSummaryResponse, ...]

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class EvidenceClaimTraceResponse(BaseModel):
    claim_id: UUID
    claim_index: int
    claim_text: str
    verdict: str | None
    cited_chunk_ids: tuple[UUID, ...]
    supported_chunk_ids: tuple[UUID, ...]
    allowed_chunk_ids: tuple[UUID, ...]
    issue_ids: tuple[UUID, ...]

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class EvidenceIssueTraceResponse(BaseModel):
    issue_id: UUID
    issue_type: str
    severity: str
    verdict: str | None
    message: str
    rationale: str
    repair_hint: str

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class EvidenceChunkRefResponse(BaseModel):
    chunk_id: UUID
    source_id: UUID
    source_title: str | None
    chunk_index: int
    excerpt_text: str

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class EvidenceSourceRefResponse(BaseModel):
    source_id: UUID
    canonical_key: str
    title: str | None
    identifiers: dict[str, object]

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class SectionEvidenceTraceResponse(BaseModel):
    section_id: str
    section_title: str
    section_order: int
    canonical_text: str
    canonical_summary: str
    repaired: bool
    latest_evaluation_result_id: UUID | None
    repair_result_id: UUID | None
    claims: tuple[EvidenceClaimTraceResponse, ...]
    issues: tuple[EvidenceIssueTraceResponse, ...]
    evidence_chunks: tuple[EvidenceChunkRefResponse, ...]
    source_refs: tuple[EvidenceSourceRefResponse, ...]
    unresolved_quality_findings: tuple[EvidenceIssueTraceResponse, ...]

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class ChunkDetailResponse(BaseModel):
    chunk_id: UUID
    source_id: UUID
    source_title: str | None
    source_url: str | None
    identifiers: dict[str, object]
    chunk_text: str
    chunk_index: int
    context_chunks: tuple[EvidenceChunkRefResponse, ...]
    run_ids: tuple[UUID, ...]
    section_ids: tuple[str, ...]

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class SourceDetailResponse(BaseModel):
    source_id: UUID
    canonical_key: str
    title: str | None
    authors: tuple[str, ...]
    venue: str | None
    year: int | None
    url: str | None
    provider_metadata: dict[str, object]
    identifiers: dict[str, object]
    run_usage_count: int

    model_config = ConfigDict(extra="forbid", from_attributes=True)
