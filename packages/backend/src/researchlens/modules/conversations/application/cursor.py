import base64
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from researchlens.shared.errors import ValidationError


@dataclass(frozen=True, slots=True)
class ConversationListCursor:
    activity_at: datetime
    conversation_id: UUID


def encode_conversation_cursor(cursor: ConversationListCursor) -> str:
    payload = {
        "activity_at": cursor.activity_at.isoformat(),
        "conversation_id": str(cursor.conversation_id),
    }
    return base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")


def decode_conversation_cursor(cursor: str) -> ConversationListCursor:
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        payload = json.loads(decoded)
        return ConversationListCursor(
            activity_at=datetime.fromisoformat(payload["activity_at"]),
            conversation_id=UUID(payload["conversation_id"]),
        )
    except Exception as exc:  # pragma: no cover - defensive path
        raise ValidationError("Conversation cursor is invalid.") from exc
