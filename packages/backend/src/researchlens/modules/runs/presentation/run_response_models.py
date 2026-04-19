from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RunSummaryResponse(BaseModel):
    id: UUID
    project_id: UUID
    conversation_id: UUID | None
    status: str
    current_stage: str | None
    output_type: str
    client_request_id: str | None
    retry_count: int
    cancel_requested: bool
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    failure_reason: str | None
    error_code: str | None
    last_event_number: int
    display_status: str
    display_stage: str
    can_stop: bool
    can_retry: bool

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class CreateRunResponse(BaseModel):
    run: RunSummaryResponse
    idempotent_replay: bool

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class RunEventResponse(BaseModel):
    run_id: UUID
    event_number: int
    event_type: str
    audience: str
    level: str
    status: str
    stage: str | None
    display_status: str
    display_stage: str
    message: str
    retry_count: int
    cancel_requested: bool
    payload: dict[str, Any] | None
    ts: datetime

    model_config = ConfigDict(extra="forbid", from_attributes=True)
