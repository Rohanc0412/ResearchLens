from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class EvidenceSectionSummary:
    section_id: str
    title: str
    section_order: int
    repaired: bool
    issue_count: int


@dataclass(frozen=True, slots=True)
class RunEvidenceSummary:
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
    sections: tuple[EvidenceSectionSummary, ...]


@dataclass(frozen=True, slots=True)
class EvidenceClaimTrace:
    claim_id: UUID
    claim_index: int
    claim_text: str
    verdict: str | None
    cited_chunk_ids: tuple[UUID, ...]
    supported_chunk_ids: tuple[UUID, ...]
    allowed_chunk_ids: tuple[UUID, ...]
    issue_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class EvidenceIssueTrace:
    issue_id: UUID
    issue_type: str
    severity: str
    verdict: str | None
    message: str
    rationale: str
    repair_hint: str


@dataclass(frozen=True, slots=True)
class EvidenceChunkRef:
    chunk_id: UUID
    source_id: UUID
    source_title: str | None
    chunk_index: int
    excerpt_text: str


@dataclass(frozen=True, slots=True)
class EvidenceSourceRef:
    source_id: UUID
    canonical_key: str
    title: str | None
    identifiers: dict[str, object]


@dataclass(frozen=True, slots=True)
class SectionEvidenceTrace:
    section_id: str
    section_title: str
    section_order: int
    canonical_text: str
    canonical_summary: str
    repaired: bool
    latest_evaluation_result_id: UUID | None
    repair_result_id: UUID | None
    claims: tuple[EvidenceClaimTrace, ...]
    issues: tuple[EvidenceIssueTrace, ...]
    evidence_chunks: tuple[EvidenceChunkRef, ...]
    source_refs: tuple[EvidenceSourceRef, ...]
    unresolved_quality_findings: tuple[EvidenceIssueTrace, ...]


@dataclass(frozen=True, slots=True)
class ChunkDetail:
    chunk_id: UUID
    source_id: UUID
    source_title: str | None
    source_url: str | None
    identifiers: dict[str, object]
    chunk_text: str
    chunk_index: int
    context_chunks: tuple[EvidenceChunkRef, ...]
    run_ids: tuple[UUID, ...]
    section_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SourceDetail:
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
