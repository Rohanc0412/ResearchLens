from dataclasses import dataclass, replace
from datetime import datetime
from typing import cast
from uuid import UUID

from researchlens.modules.runs.domain.run_stage import RunStage, normalize_run_stage
from researchlens.modules.runs.domain.run_status import RunStatus
from researchlens.shared.errors import ValidationError

MAX_OUTPUT_TYPE_LENGTH = 64
MAX_CLIENT_REQUEST_ID_LENGTH = 200
MAX_FAILURE_REASON_LENGTH = 4000
MAX_ERROR_CODE_LENGTH = 120
UNSET = object()


def normalize_output_type(output_type: str) -> str:
    normalized = output_type.strip()
    if not normalized:
        raise ValidationError("Output type is required.")
    if len(normalized) > MAX_OUTPUT_TYPE_LENGTH:
        raise ValidationError("Output type must be 64 characters or fewer.")
    return normalized


def normalize_client_request_id(client_request_id: str | None) -> str | None:
    if client_request_id is None:
        return None
    normalized = client_request_id.strip()
    if not normalized:
        raise ValidationError("Client request id cannot be blank.")
    if len(normalized) > MAX_CLIENT_REQUEST_ID_LENGTH:
        raise ValidationError("Client request id must be 200 characters or fewer.")
    return normalized


def normalize_failure_reason(failure_reason: str | None) -> str | None:
    if failure_reason is None:
        return None
    normalized = failure_reason.strip()
    if not normalized:
        return None
    if len(normalized) > MAX_FAILURE_REASON_LENGTH:
        raise ValidationError("Failure reason must be 4000 characters or fewer.")
    return normalized


def normalize_error_code(error_code: str | None) -> str | None:
    if error_code is None:
        return None
    normalized = error_code.strip()
    if not normalized:
        return None
    if len(normalized) > MAX_ERROR_CODE_LENGTH:
        raise ValidationError("Error code must be 120 characters or fewer.")
    return normalized


@dataclass(frozen=True, slots=True)
class Run:
    id: UUID
    tenant_id: UUID
    project_id: UUID
    conversation_id: UUID | None
    created_by_user_id: UUID
    status: RunStatus
    current_stage: RunStage | None
    output_type: str
    trigger_message_id: UUID | None
    client_request_id: str | None
    cancel_requested_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    retry_count: int
    failure_reason: str | None
    error_code: str | None
    last_event_number: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        id: UUID,
        tenant_id: UUID,
        project_id: UUID,
        conversation_id: UUID | None,
        created_by_user_id: UUID,
        output_type: str,
        trigger_message_id: UUID | None,
        client_request_id: str | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Run":
        return cls(
            id=id,
            tenant_id=tenant_id,
            project_id=project_id,
            conversation_id=conversation_id,
            created_by_user_id=created_by_user_id,
            status=RunStatus.CREATED,
            current_stage=RunStage.RETRIEVE,
            output_type=normalize_output_type(output_type),
            trigger_message_id=trigger_message_id,
            client_request_id=normalize_client_request_id(client_request_id),
            cancel_requested_at=None,
            started_at=None,
            finished_at=None,
            retry_count=0,
            failure_reason=None,
            error_code=None,
            last_event_number=0,
            created_at=created_at,
            updated_at=updated_at,
        )

    def replace_values(
        self,
        *,
        status: RunStatus | None = None,
        current_stage: RunStage | str | None | object = UNSET,
        cancel_requested_at: datetime | None | object = UNSET,
        started_at: datetime | None | object = UNSET,
        finished_at: datetime | None | object = UNSET,
        retry_count: int | None = None,
        failure_reason: str | None | object = UNSET,
        error_code: str | None | object = UNSET,
        last_event_number: int | None = None,
        updated_at: datetime | None = None,
    ) -> "Run":
        current_stage_value = (
            self.current_stage
            if current_stage is UNSET
            else normalize_run_stage(cast(RunStage | str | None, current_stage))
        )
        cancel_requested_at_value = (
            self.cancel_requested_at
            if cancel_requested_at is UNSET
            else cast(datetime | None, cancel_requested_at)
        )
        started_at_value = (
            self.started_at if started_at is UNSET else cast(datetime | None, started_at)
        )
        finished_at_value = (
            self.finished_at
            if finished_at is UNSET
            else cast(datetime | None, finished_at)
        )
        failure_reason_value = (
            self.failure_reason
            if failure_reason is UNSET
            else normalize_failure_reason(cast(str | None, failure_reason))
        )
        error_code_value = (
            self.error_code
            if error_code is UNSET
            else normalize_error_code(cast(str | None, error_code))
        )
        return replace(
            self,
            status=status or self.status,
            current_stage=current_stage_value,
            cancel_requested_at=cancel_requested_at_value,
            started_at=started_at_value,
            finished_at=finished_at_value,
            retry_count=self.retry_count if retry_count is None else retry_count,
            failure_reason=failure_reason_value,
            error_code=error_code_value,
            last_event_number=(
                self.last_event_number
                if last_event_number is None
                else last_event_number
            ),
            updated_at=self.updated_at if updated_at is None else updated_at,
        )
