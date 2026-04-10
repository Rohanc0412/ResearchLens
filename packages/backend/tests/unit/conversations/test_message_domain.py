from datetime import UTC, datetime
from uuid import uuid4

import pytest

from researchlens.modules.conversations.domain import Message, MessageRole, MessageType
from researchlens.shared.errors import ValidationError


def test_message_create_accepts_text_message() -> None:
    message = Message.create(
        id=uuid4(),
        tenant_id=uuid4(),
        conversation_id=uuid4(),
        role=MessageRole.USER,
        type=MessageType.TEXT,
        content_text="  hello  ",
        content_json=None,
        metadata_json=None,
        created_at=datetime.now(tz=UTC),
        client_message_id=" client-1 ",
    )

    assert message.content_text == "hello"
    assert message.client_message_id == "client-1"


def test_message_create_rejects_missing_text_for_text_type() -> None:
    with pytest.raises(ValidationError):
        Message.create(
            id=uuid4(),
            tenant_id=uuid4(),
            conversation_id=uuid4(),
            role=MessageRole.USER,
            type=MessageType.TEXT,
            content_text=None,
            content_json={"value": "ignored"},
            metadata_json=None,
            created_at=datetime.now(tz=UTC),
            client_message_id=None,
        )


def test_message_create_rejects_blank_client_message_id() -> None:
    with pytest.raises(ValidationError):
        Message.create(
            id=uuid4(),
            tenant_id=uuid4(),
            conversation_id=uuid4(),
            role=MessageRole.USER,
            type=MessageType.TEXT,
            content_text="hello",
            content_json=None,
            metadata_json=None,
            created_at=datetime.now(tz=UTC),
            client_message_id="   ",
        )
