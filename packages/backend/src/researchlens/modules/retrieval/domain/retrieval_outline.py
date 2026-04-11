from dataclasses import dataclass

from researchlens.shared.errors import ValidationError


@dataclass(frozen=True, slots=True)
class RetrievalOutlineSection:
    section_id: str
    title: str
    goal: str
    suggested_evidence_themes: tuple[str, ...]
    key_points: tuple[str, ...]
    section_order: int


@dataclass(frozen=True, slots=True)
class RetrievalOutline:
    report_title: str
    sections: tuple[RetrievalOutlineSection, ...]

    def __post_init__(self) -> None:
        if not self.report_title.strip():
            raise ValidationError("Retrieval outline title is required.")
        if not self.sections:
            raise ValidationError("Retrieval outline must include at least one section.")
        ids = [section.section_id for section in self.sections]
        if len(ids) != len(set(ids)):
            raise ValidationError("Retrieval outline section ids must be unique.")
        titles = [section.title.casefold().strip() for section in self.sections]
        if len(titles) != len(set(titles)):
            raise ValidationError("Retrieval outline section titles must be unique.")
