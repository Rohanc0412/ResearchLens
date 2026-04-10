from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateConversationRequest(BaseModel):
    title: str

    model_config = ConfigDict(extra="forbid")


class UpdateConversationRequest(BaseModel):
    title: str

    model_config = ConfigDict(extra="forbid")


class ConversationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    project_id: UUID | None
    created_by_user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    next_cursor: str | None

    model_config = ConfigDict(extra="forbid")


class PostMessageRequest(BaseModel):
    role: str
    type: str
    content_text: str | None = None
    content_json: dict[str, Any] | list[Any] | None = None
    metadata_json: dict[str, Any] | None = None
    client_message_id: str | None = None

    model_config = ConfigDict(extra="forbid")


class MessageResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    conversation_id: UUID
    role: str
    type: str
    content_text: str | None
    content_json: dict[str, Any] | list[Any] | None
    metadata_json: dict[str, Any] | None
    created_at: datetime
    client_message_id: str | None

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class MessageWriteResponse(MessageResponse):
    idempotent_replay: bool

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class RecordRunTriggerRequest(BaseModel):
    source_message_id: UUID | None = None
    request_text: str
    client_request_id: str | None = None

    model_config = ConfigDict(extra="forbid")


class RunTriggerResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    conversation_id: UUID
    project_id: UUID | None
    source_message_id: UUID | None
    request_text: str
    client_request_id: str | None
    status: str
    created_by_user_id: UUID
    created_at: datetime

    model_config = ConfigDict(extra="forbid", from_attributes=True)
