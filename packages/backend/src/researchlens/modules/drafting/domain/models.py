from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.drafting.domain.citation_tokens import (
    ensure_only_valid_citation_tokens,
    normalize_citation_tokens,
)
from researchlens.shared.errors import ValidationError


def _clean_text(value: str, *, field_name: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ValidationError(f"{field_name} is required.")
    return normalized


@dataclass(frozen=True, slots=True)
class AllowedEvidenceItem:
    tenant_id: UUID
    run_id: UUID
    chunk_id: UUID
    source_id: UUID
    source_rank: int
    chunk_index: int
    title: str
    text_excerpt: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", _clean_text(self.title, field_name="Evidence title"))
        object.__setattr__(
            self,
            "text_excerpt",
            _clean_text(self.text_excerpt, field_name="Evidence excerpt"),
        )


@dataclass(frozen=True, slots=True)
class EvidencePack:
    tenant_id: UUID
    run_id: UUID
    section_id: str
    items: tuple[AllowedEvidenceItem, ...]

    def __post_init__(self) -> None:
        section_id = _clean_text(self.section_id, field_name="Section id")
        if not self.items:
            raise ValidationError(f"Section '{section_id}' has an empty evidence pack.")
        ordered = tuple(
            sorted(
                self.items,
                key=lambda item: (
                    item.source_rank,
                    item.chunk_index,
                    str(item.chunk_id),
                ),
            )
        )
        for item in ordered:
            if item.tenant_id != self.tenant_id or item.run_id != self.run_id:
                raise ValidationError("Evidence pack items must belong to the same tenant and run.")
        object.__setattr__(self, "section_id", section_id)
        object.__setattr__(self, "items", ordered)

    @property
    def allowed_chunk_ids(self) -> frozenset[UUID]:
        return frozenset(item.chunk_id for item in self.items)


@dataclass(frozen=True, slots=True)
class DraftingSection:
    run_id: UUID
    tenant_id: UUID
    section_id: str
    title: str
    section_order: int
    goal: str
    key_points: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "section_id",
            _clean_text(self.section_id, field_name="Section id"),
        )
        object.__setattr__(self, "title", _clean_text(self.title, field_name="Section title"))
        object.__setattr__(self, "goal", _clean_text(self.goal, field_name="Section goal"))
        if self.section_order < 1:
            raise ValidationError("Section order must be positive.")


@dataclass(frozen=True, slots=True)
class SectionBrief:
    report_title: str
    section: DraftingSection
    evidence_pack: EvidencePack
    evidence_summary: str
    prior_continuity_summary: str | None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "report_title",
            _clean_text(self.report_title, field_name="Report title"),
        )
        if self.prior_continuity_summary is not None and not self.prior_continuity_summary.strip():
            raise ValidationError("Continuity summary cannot be blank.")


@dataclass(frozen=True, slots=True)
class SectionDraft:
    run_id: UUID
    tenant_id: UUID
    section: DraftingSection
    section_text: str
    section_summary: str
    status: str
    provider_name: str
    model_name: str

    def __post_init__(self) -> None:
        section_text = normalize_citation_tokens(self.section_text.strip())
        if not section_text:
            raise ValidationError("Section text is required.")
        if section_text.startswith("#"):
            raise ValidationError("Section text must not contain markdown headings.")
        ensure_only_valid_citation_tokens(section_text)
        summary = self.section_summary.strip()
        if not summary:
            raise ValidationError("Section summary is required.")
        if "[[chunk:" in summary:
            raise ValidationError("Section summary must not contain citations.")
        object.__setattr__(self, "section_text", section_text)
        object.__setattr__(self, "section_summary", summary)
        object.__setattr__(self, "status", _clean_text(self.status, field_name="Section status"))
        object.__setattr__(
            self,
            "provider_name",
            _clean_text(self.provider_name, field_name="Provider name"),
        )
        object.__setattr__(
            self,
            "model_name",
            _clean_text(self.model_name, field_name="Model name"),
        )


@dataclass(frozen=True, slots=True)
class ReportDraft:
    run_id: UUID
    tenant_id: UUID
    title: str
    markdown_text: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", _clean_text(self.title, field_name="Report title"))
        markdown_text = self.markdown_text.strip()
        if not markdown_text:
            raise ValidationError("Report markdown is required.")
        object.__setattr__(self, "markdown_text", markdown_text)
