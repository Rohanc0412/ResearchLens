from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from researchlens.shared.errors import ValidationError

MAX_RUN_TRIGGER_TEXT_LENGTH = 4000
MAX_CLIENT_REQUEST_ID_LENGTH = 200


class RunTriggerStatus(StrEnum):
    RECORDED = "recorded"


def normalize_run_trigger_text(request_text: str) -> str:
    normalized_text = request_text.strip()
    if not normalized_text:
        raise ValidationError("Run trigger request text is required.")
    if len(normalized_text) > MAX_RUN_TRIGGER_TEXT_LENGTH:
        raise ValidationError("Run trigger request text must be 4000 characters or fewer.")
    return normalized_text


def normalize_client_request_id(client_request_id: str | None) -> str | None:
    if client_request_id is None:
        return None
    normalized_client_request_id = client_request_id.strip()
    if not normalized_client_request_id:
        raise ValidationError("Client request id cannot be blank.")
    if len(normalized_client_request_id) > MAX_CLIENT_REQUEST_ID_LENGTH:
        raise ValidationError("Client request id must be 200 characters or fewer.")
    return normalized_client_request_id


@dataclass(frozen=True, slots=True)
class RunTrigger:
    id: UUID
    tenant_id: UUID
    conversation_id: UUID
    project_id: UUID | None
    source_message_id: UUID | None
    request_text: str
    client_request_id: str | None
    status: RunTriggerStatus
    created_by_user_id: UUID
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        id: UUID,
        tenant_id: UUID,
        conversation_id: UUID,
        project_id: UUID | None,
        source_message_id: UUID | None,
        request_text: str,
        client_request_id: str | None,
        created_by_user_id: UUID,
        created_at: datetime,
    ) -> "RunTrigger":
        return cls(
            id=id,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            project_id=project_id,
            source_message_id=source_message_id,
            request_text=normalize_run_trigger_text(request_text),
            client_request_id=normalize_client_request_id(client_request_id),
            status=RunTriggerStatus.RECORDED,
            created_by_user_id=created_by_user_id,
            created_at=created_at,
        )
