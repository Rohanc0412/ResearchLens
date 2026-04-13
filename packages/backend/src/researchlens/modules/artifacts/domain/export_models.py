from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class FinalSection:
    section_id: str
    title: str
    section_order: int
    text: str
    summary: str
    repaired: bool
    draft_id: UUID
    repair_result_id: UUID | None


@dataclass(frozen=True, slots=True)
class ExportSource:
    source_id: UUID
    canonical_key: str
    title: str | None
    identifiers: dict[str, object]
    metadata: dict[str, object]


@dataclass(frozen=True, slots=True)
class ExportChunk:
    chunk_id: UUID
    source_id: UUID
    chunk_index: int
    text: str


@dataclass(frozen=True, slots=True)
class CitationReference:
    citation_label: str
    chunk_id: UUID
    source_id: UUID


@dataclass(frozen=True, slots=True)
class ReportExportBundle:
    tenant_id: UUID
    project_id: UUID
    run_id: UUID
    conversation_id: UUID | None
    report_title: str
    sections: tuple[FinalSection, ...]
    chunks: tuple[ExportChunk, ...]
    sources: tuple[ExportSource, ...]
    citations: tuple[CitationReference, ...]
    latest_evaluation_pass_id: UUID | None
    latest_repair_pass_id: UUID | None
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RenderedArtifact:
    kind: str
    filename: str
    media_type: str
    content: bytes
    metadata: dict[str, object]


@dataclass(frozen=True, slots=True)
class PersistedArtifact:
    id: UUID
    run_id: UUID
    kind: str
    filename: str
    media_type: str
    storage_backend: str
    storage_key: str
    byte_size: int
    sha256: str
    created_at: datetime
    manifest_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PersistedManifest:
    id: UUID
    run_id: UUID
    report_title: str
    artifact_ids: tuple[UUID, ...]
    created_at: datetime
