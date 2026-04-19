from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from researchlens.modules.runs.application.display import (
    display_stage_for,
    display_status_for,
)
from researchlens.modules.runs.domain import (
    Run,
    RunCheckpointRecord,
    RunEventRecord,
    RunStage,
    RunStatus,
)


@dataclass(frozen=True, slots=True)
class RunSummaryView:
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


@dataclass(frozen=True, slots=True)
class CreateRunResult:
    run: RunSummaryView
    idempotent_replay: bool


@dataclass(frozen=True, slots=True)
class RunEventView:
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


@dataclass(frozen=True, slots=True)
class RetryDecision:
    resume_from_stage: RunStage
    message: str
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ResumeState:
    start_stage: RunStage
    completed_stages: tuple[RunStage, ...]
    latest_checkpoint: RunCheckpointRecord | None


def to_run_summary_view(run: Run) -> RunSummaryView:
    cancel_requested = run.cancel_requested_at is not None
    return RunSummaryView(
        id=run.id,
        project_id=run.project_id,
        conversation_id=run.conversation_id,
        status=run.status.value,
        current_stage=run.current_stage.value if run.current_stage is not None else None,
        output_type=run.output_type,
        client_request_id=run.client_request_id,
        retry_count=run.retry_count,
        cancel_requested=cancel_requested,
        created_at=run.created_at,
        updated_at=run.updated_at,
        started_at=run.started_at,
        finished_at=run.finished_at,
        failure_reason=run.failure_reason,
        error_code=run.error_code,
        last_event_number=run.last_event_number,
        display_status=display_status_for(run.status),
        display_stage=display_stage_for(
            stage=run.current_stage,
            status=run.status,
            cancel_requested=cancel_requested,
            started_at=run.started_at,
        ),
        can_stop=run.status in {RunStatus.QUEUED, RunStatus.RUNNING} and not cancel_requested,
        can_retry=run.status == RunStatus.FAILED,
    )


def to_run_event_view(event: RunEventRecord) -> RunEventView:
    return RunEventView(
        run_id=event.run_id,
        event_number=event.event_number,
        event_type=event.event_type.value,
        audience=event.audience.value,
        level=event.level.value,
        status=event.status.value,
        stage=event.stage.value if event.stage is not None else None,
        display_status=display_status_for(event.status),
        display_stage=display_stage_for(
            stage=event.stage,
            status=event.status,
            cancel_requested=event.cancel_requested,
            started_at=None,
        ),
        message=event.message,
        retry_count=event.retry_count,
        cancel_requested=event.cancel_requested,
        payload=event.payload_json,
        ts=event.created_at,
    )
