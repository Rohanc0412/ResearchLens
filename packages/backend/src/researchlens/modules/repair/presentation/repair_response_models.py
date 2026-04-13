from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RepairSectionResponse(BaseModel):
    section_id: str
    section_title: str
    section_order: int
    status: str
    action: str
    changed: bool
    evaluation_section_result_id: UUID
    repair_result_id: UUID
    reevaluation_pass_id: UUID | None
    unresolved_reason: str | None

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class RepairSummaryResponse(BaseModel):
    repair_pass_id: UUID | None
    run_id: UUID
    status: str
    selected_count: int
    changed_count: int
    unresolved_count: int
    sections: tuple[RepairSectionResponse, ...]

    model_config = ConfigDict(extra="forbid", from_attributes=True)
