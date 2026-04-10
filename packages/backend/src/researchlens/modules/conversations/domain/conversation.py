from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from researchlens.shared.errors import ValidationError

MAX_CONVERSATION_TITLE_LENGTH = 200


def normalize_conversation_title(title: str) -> str:
    normalized_title = title.strip()
    if not normalized_title:
        raise ValidationError("Conversation title is required.")
    if len(normalized_title) > MAX_CONVERSATION_TITLE_LENGTH:
        raise ValidationError("Conversation title must be 200 characters or fewer.")
    return normalized_title


@dataclass(frozen=True, slots=True)
class Conversation:
    id: UUID
    tenant_id: UUID
    project_id: UUID | None
    created_by_user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None

    @classmethod
    def create(
        cls,
        *,
        id: UUID,
        tenant_id: UUID,
        project_id: UUID | None,
        created_by_user_id: UUID,
        title: str,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Conversation":
        return cls(
            id=id,
            tenant_id=tenant_id,
            project_id=project_id,
            created_by_user_id=created_by_user_id,
            title=normalize_conversation_title(title),
            created_at=created_at,
            updated_at=updated_at,
            last_message_at=None,
        )

    def update_title(self, *, title: str, updated_at: datetime) -> "Conversation":
        return replace(
            self,
            title=normalize_conversation_title(title),
            updated_at=updated_at,
        )

    def record_message(self, *, message_created_at: datetime) -> "Conversation":
        return replace(
            self,
            updated_at=message_created_at,
            last_message_at=message_created_at,
        )
