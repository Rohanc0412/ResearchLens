from researchlens.modules.runs.domain import (
    Run,
    RunCheckpointRecord,
    RunEventAudience,
    RunEventLevel,
    RunEventRecord,
    RunEventType,
    RunQueueItem,
    RunStage,
    RunStatus,
    RunTransitionRecord,
)
from researchlens.modules.runs.infrastructure.rows import (
    RunCheckpointRow,
    RunEventRow,
    RunQueueItemRow,
    RunRow,
    RunTransitionRow,
)


def to_run_domain(row: RunRow) -> Run:
    return Run(
        id=row.id,
        tenant_id=row.tenant_id,
        project_id=row.project_id,
        conversation_id=row.conversation_id,
        created_by_user_id=row.created_by_user_id,
        status=RunStatus(row.status),
        current_stage=RunStage(row.current_stage) if row.current_stage else None,
        output_type=row.output_type,
        trigger_message_id=row.trigger_message_id,
        client_request_id=row.client_request_id,
        cancel_requested_at=row.cancel_requested_at,
        started_at=row.started_at,
        finished_at=row.finished_at,
        retry_count=row.retry_count,
        failure_reason=row.failure_reason,
        error_code=row.error_code,
        last_event_number=row.last_event_number,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def update_run_row(row: RunRow, run: Run) -> None:
    row.project_id = run.project_id
    row.conversation_id = run.conversation_id
    row.status = run.status.value
    row.current_stage = run.current_stage.value if run.current_stage else None
    row.output_type = run.output_type
    row.trigger_message_id = run.trigger_message_id
    row.client_request_id = run.client_request_id
    row.cancel_requested_at = run.cancel_requested_at
    row.started_at = run.started_at
    row.finished_at = run.finished_at
    row.retry_count = run.retry_count
    row.failure_reason = run.failure_reason
    row.error_code = run.error_code
    row.updated_at = run.updated_at


def to_event_domain(row: RunEventRow) -> RunEventRecord:
    return RunEventRecord(
        id=row.id,
        run_id=row.run_id,
        event_number=row.event_number,
        event_type=RunEventType(row.event_type),
        audience=RunEventAudience(row.audience),
        level=RunEventLevel(row.level),
        status=RunStatus(row.status),
        stage=RunStage(row.stage) if row.stage else None,
        message=row.message,
        payload_json=row.payload_json,
        retry_count=row.retry_count,
        cancel_requested=row.cancel_requested,
        created_at=row.created_at,
        event_key=row.event_key,
    )


def to_checkpoint_domain(row: RunCheckpointRow) -> RunCheckpointRecord:
    return RunCheckpointRecord(
        id=row.id,
        run_id=row.run_id,
        stage=RunStage(row.stage),
        checkpoint_key=row.checkpoint_key,
        payload_json=row.payload_json,
        summary_json=row.summary_json,
        created_at=row.created_at,
    )


def to_transition_domain(row: RunTransitionRow) -> RunTransitionRecord:
    return RunTransitionRecord(
        id=row.id,
        run_id=row.run_id,
        from_status=RunStatus(row.from_status),
        to_status=RunStatus(row.to_status),
        changed_at=row.changed_at,
        reason=row.reason,
    )


def to_queue_item_domain(row: RunQueueItemRow) -> RunQueueItem:
    return RunQueueItem(
        id=row.id,
        tenant_id=row.tenant_id,
        run_id=row.run_id,
        job_type=row.job_type,
        status=row.status,
        available_at=row.available_at,
        lease_token=row.lease_token,
        leased_at=row.leased_at,
        lease_expires_at=row.lease_expires_at,
        attempts=row.attempts,
        last_error=row.last_error,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
