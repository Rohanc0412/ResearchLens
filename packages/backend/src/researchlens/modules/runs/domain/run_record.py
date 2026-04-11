from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from researchlens.modules.runs.domain.run_stage import RunStage
from researchlens.modules.runs.domain.run_status import RunStatus


@dataclass(frozen=True, slots=True)
class RunTransitionRecord:
    id: UUID
    run_id: UUID
    from_status: RunStatus
    to_status: RunStatus
    changed_at: datetime
    reason: str | None


@dataclass(frozen=True, slots=True)
class RunCheckpointRecord:
    id: UUID
    run_id: UUID
    stage: RunStage
    checkpoint_key: str
    payload_json: dict[str, Any] | None
    summary_json: dict[str, Any] | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RunQueueItem:
    id: UUID
    tenant_id: UUID
    run_id: UUID
    job_type: str
    status: str
    available_at: datetime
    lease_token: UUID | None
    leased_at: datetime | None
    lease_expires_at: datetime | None
    attempts: int
    last_error: str | None
    created_at: datetime
    updated_at: datetime
