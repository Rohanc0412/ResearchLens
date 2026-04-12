from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SectionDraftPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    section_id: str
    section_text: str
    section_summary: str
    status: Literal["completed"] = "completed"

    @field_validator("section_id", "section_text", "section_summary")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value is required.")
        return normalized


class SectionPlanRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    section_id: str
    title: str
    section_order: int = Field(ge=1)
    goal: str
    key_points: tuple[str, ...] = ()


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: UUID
    run_id: UUID
    source_id: UUID
    chunk_id: UUID
    source_rank: int = Field(ge=1)
    chunk_index: int = Field(ge=0)
    target_section: str | None = None
    source_title: str
    chunk_text: str


class RunDraftingInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: UUID
    run_id: UUID
    report_title: str
    research_question: str
    sections: tuple[SectionPlanRecord, ...]
    evidence: tuple[EvidenceRecord, ...]
