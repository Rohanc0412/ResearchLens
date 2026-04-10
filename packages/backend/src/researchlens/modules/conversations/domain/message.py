from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from researchlens.shared.errors import ValidationError

MAX_MESSAGE_TEXT_LENGTH = 20000
MAX_CLIENT_MESSAGE_ID_LENGTH = 200


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageType(StrEnum):
    TEXT = "text"
    STRUCTURED = "structured"
    MIXED = "mixed"


def normalize_message_text(content_text: str | None) -> str | None:
    if content_text is None:
        return None
    normalized_text = content_text.strip()
    if not normalized_text:
        return None
    if len(normalized_text) > MAX_MESSAGE_TEXT_LENGTH:
        raise ValidationError("Message text must be 20000 characters or fewer.")
    return normalized_text


def normalize_client_message_id(client_message_id: str | None) -> str | None:
    if client_message_id is None:
        return None
    normalized_client_message_id = client_message_id.strip()
    if not normalized_client_message_id:
        raise ValidationError("Client message id cannot be blank.")
    if len(normalized_client_message_id) > MAX_CLIENT_MESSAGE_ID_LENGTH:
        raise ValidationError("Client message id must be 200 characters or fewer.")
    return normalized_client_message_id


@dataclass(frozen=True, slots=True)
class Message:
    id: UUID
    tenant_id: UUID
    conversation_id: UUID
    role: MessageRole
    type: MessageType
    content_text: str | None
    content_json: dict[str, Any] | list[Any] | None
    metadata_json: dict[str, Any] | None
    created_at: datetime
    client_message_id: str | None

    @classmethod
    def create(
        cls,
        *,
        id: UUID,
        tenant_id: UUID,
        conversation_id: UUID,
        role: MessageRole,
        type: MessageType,
        content_text: str | None,
        content_json: dict[str, Any] | list[Any] | None,
        metadata_json: dict[str, Any] | None,
        created_at: datetime,
        client_message_id: str | None,
    ) -> "Message":
        normalized_text = normalize_message_text(content_text)
        normalized_client_message_id = normalize_client_message_id(client_message_id)
        _validate_message_payload(
            message_type=type,
            content_text=normalized_text,
            content_json=content_json,
        )
        return cls(
            id=id,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            role=role,
            type=type,
            content_text=normalized_text,
            content_json=content_json,
            metadata_json=metadata_json,
            created_at=created_at,
            client_message_id=normalized_client_message_id,
        )


def _validate_message_payload(
    *,
    message_type: MessageType,
    content_text: str | None,
    content_json: dict[str, Any] | list[Any] | None,
) -> None:
    if content_text is None and content_json is None:
        raise ValidationError("Message content is required.")
    if message_type is MessageType.TEXT and content_text is None:
        raise ValidationError("Text messages require content_text.")
    if message_type is MessageType.STRUCTURED and content_json is None:
        raise ValidationError("Structured messages require content_json.")
    if message_type is MessageType.MIXED and (content_text is None or content_json is None):
        raise ValidationError("Mixed messages require content_text and content_json.")
