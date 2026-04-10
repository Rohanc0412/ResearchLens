from datetime import UTC, datetime
from uuid import uuid4

import pytest

from researchlens.modules.conversations.application.cursor import (
    ConversationListCursor,
    decode_conversation_cursor,
    encode_conversation_cursor,
)
from researchlens.shared.errors import ValidationError


def test_conversation_cursor_round_trip() -> None:
    cursor = ConversationListCursor(
        activity_at=datetime.now(tz=UTC),
        conversation_id=uuid4(),
    )

    decoded = decode_conversation_cursor(encode_conversation_cursor(cursor))

    assert decoded == cursor


def test_conversation_cursor_rejects_invalid_value() -> None:
    with pytest.raises(ValidationError):
        decode_conversation_cursor("invalid")
