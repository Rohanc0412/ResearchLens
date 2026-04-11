from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from researchlens.modules.runs.domain.run_stage import RunStage
from researchlens.modules.runs.domain.run_status import RunStatus


class RunEventAudience(StrEnum):
    PROGRESS = "progress"
    DIAGNOSTIC = "diagnostic"
    STATE = "state"


class RunEventLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class RunEventType(StrEnum):
    RUN_CREATED = "run.created"
    RUN_QUEUED = "run.queued"
    RUN_RUNNING = "run.running"
    RUN_CANCELED = "run.canceled"
    RUN_FAILED = "run.failed"
    RUN_SUCCEEDED = "run.succeeded"
    CANCEL_REQUESTED = "cancel.requested"
    RETRY_REQUESTED = "retry.requested"
    STAGE_STARTED = "stage.started"
    STAGE_COMPLETED = "stage.completed"
    STAGE_FAILED = "stage.failed"
    CHECKPOINT_WRITTEN = "checkpoint.written"


@dataclass(frozen=True, slots=True)
class RunEventRecord:
    id: UUID
    run_id: UUID
    event_number: int
    event_type: RunEventType
    audience: RunEventAudience
    level: RunEventLevel
    status: RunStatus
    stage: RunStage | None
    message: str
    payload_json: dict[str, Any] | None
    retry_count: int
    cancel_requested: bool
    created_at: datetime
    event_key: str | None
