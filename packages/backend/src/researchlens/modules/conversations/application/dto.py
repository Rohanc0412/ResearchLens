from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from researchlens.modules.conversations.application.cursor import (
    ConversationListCursor,
    encode_conversation_cursor,
)
from researchlens.modules.conversations.domain import Conversation, Message, RunTrigger


@dataclass(frozen=True, slots=True)
class ConversationView:
    id: UUID
    tenant_id: UUID
    project_id: UUID | None
    created_by_user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None


@dataclass(frozen=True, slots=True)
class ConversationListPage:
    items: list[ConversationView]
    next_cursor: str | None


@dataclass(frozen=True, slots=True)
class MessageView:
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


@dataclass(frozen=True, slots=True)
class MessageWriteResult:
    message: MessageView
    idempotent_replay: bool


@dataclass(frozen=True, slots=True)
class RunTriggerView:
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


def to_conversation_view(conversation: Conversation) -> ConversationView:
    return ConversationView(
        id=conversation.id,
        tenant_id=conversation.tenant_id,
        project_id=conversation.project_id,
        created_by_user_id=conversation.created_by_user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        last_message_at=conversation.last_message_at,
    )


def to_conversation_list_page(conversations: list[Conversation]) -> ConversationListPage:
    items = [to_conversation_view(conversation) for conversation in conversations]
    next_cursor = None
    if conversations:
        last_conversation = conversations[-1]
        next_cursor = encode_conversation_cursor(
            ConversationListCursor(
                activity_at=last_conversation.last_message_at or last_conversation.created_at,
                conversation_id=last_conversation.id,
            )
        )
    return ConversationListPage(items=items, next_cursor=next_cursor)


def to_message_view(message: Message) -> MessageView:
    return MessageView(
        id=message.id,
        tenant_id=message.tenant_id,
        conversation_id=message.conversation_id,
        role=message.role.value,
        type=message.type.value,
        content_text=message.content_text,
        content_json=message.content_json,
        metadata_json=message.metadata_json,
        created_at=message.created_at,
        client_message_id=message.client_message_id,
    )


def to_run_trigger_view(trigger: RunTrigger) -> RunTriggerView:
    return RunTriggerView(
        id=trigger.id,
        tenant_id=trigger.tenant_id,
        conversation_id=trigger.conversation_id,
        project_id=trigger.project_id,
        source_message_id=trigger.source_message_id,
        request_text=trigger.request_text,
        client_request_id=trigger.client_request_id,
        status=trigger.status.value,
        created_by_user_id=trigger.created_by_user_id,
        created_at=trigger.created_at,
    )
