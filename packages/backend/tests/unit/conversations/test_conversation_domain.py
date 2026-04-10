from datetime import UTC, datetime
from uuid import uuid4

import pytest

from researchlens.modules.conversations.domain import Conversation
from researchlens.shared.errors import ValidationError


def test_conversation_create_trims_title() -> None:
    conversation = Conversation.create(
        id=uuid4(),
        tenant_id=uuid4(),
        project_id=uuid4(),
        created_by_user_id=uuid4(),
        title="  Working Draft  ",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )

    assert conversation.title == "Working Draft"


@pytest.mark.parametrize("value", ["", "   "])
def test_conversation_create_rejects_blank_title(value: str) -> None:
    with pytest.raises(ValidationError):
        Conversation.create(
            id=uuid4(),
            tenant_id=uuid4(),
            project_id=uuid4(),
            created_by_user_id=uuid4(),
            title=value,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
