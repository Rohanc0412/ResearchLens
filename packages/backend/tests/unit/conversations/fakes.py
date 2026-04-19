from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from researchlens.modules.conversations.application.cursor import ConversationListCursor
from researchlens.modules.conversations.application.ports import (
    ConversationRepository,
    MessageRepository,
    ProjectScopeReader,
    RunTriggerRepository,
)
from researchlens.modules.conversations.domain import Conversation, Message, RunTrigger


class FakeTransactionManager:
    @asynccontextmanager
    async def boundary(self) -> AsyncIterator[None]:
        yield


class InMemoryProjectScopeReader(ProjectScopeReader):
    def __init__(self, project_ids: set[UUID]) -> None:
        self._project_ids = project_ids

    async def project_exists_for_tenant(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
    ) -> bool:
        return project_id in self._project_ids


class InMemoryConversationRepository(ConversationRepository):
    def __init__(self, conversations: list[Conversation] | None = None) -> None:
        self._conversations = {
            conversation.id: conversation for conversation in conversations or []
        }

    async def add(self, conversation: Conversation) -> Conversation:
        self._conversations[conversation.id] = conversation
        return conversation

    async def get_by_id_for_tenant(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
    ) -> Conversation | None:
        conversation = self._conversations.get(conversation_id)
        if conversation is None or conversation.tenant_id != tenant_id:
            return None
        return conversation

    async def list_by_project(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
        limit: int,
        cursor: ConversationListCursor | None,
    ) -> list[Conversation]:
        items = [
            conversation
            for conversation in self._conversations.values()
            if conversation.tenant_id == tenant_id and conversation.project_id == project_id
        ]
        items.sort(key=_conversation_sort_key, reverse=True)
        if cursor is not None:
            items = [
                item
                for item in items
                if _conversation_sort_key(item)
                < (cursor.activity_at, cursor.conversation_id)
            ]
        return items[:limit]

    async def save(self, conversation: Conversation) -> Conversation | None:
        if conversation.id not in self._conversations:
            return None
        self._conversations[conversation.id] = conversation
        return conversation

    async def delete_by_id_for_tenant(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
    ) -> bool:
        conversation = self._conversations.get(conversation_id)
        if conversation is None or conversation.tenant_id != tenant_id:
            return False
        del self._conversations[conversation_id]
        return True


class InMemoryMessageRepository(MessageRepository):
    def __init__(self, messages: list[Message] | None = None) -> None:
        self._messages = {message.id: message for message in messages or []}

    async def add(self, message: Message) -> Message:
        self._messages[message.id] = message
        return message

    async def update_metadata(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
        metadata_json: dict[str, Any] | None,
    ) -> Message | None:
        message = await self.get_by_id_for_tenant(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=message_id,
        )
        if message is None:
            return None
        updated = replace(message, metadata_json=metadata_json)
        self._messages[message_id] = updated
        return updated

    async def get_by_id_for_tenant(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
    ) -> Message | None:
        message = self._messages.get(message_id)
        if (
            message is None
            or message.tenant_id != tenant_id
            or message.conversation_id != conversation_id
        ):
            return None
        return message

    async def get_by_client_message_id(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        client_message_id: str,
    ) -> Message | None:
        for message in self._messages.values():
            if (
                message.tenant_id == tenant_id
                and message.conversation_id == conversation_id
                and message.client_message_id == client_message_id
            ):
                return message
        return None

    async def list_by_conversation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
    ) -> list[Message]:
        return sorted(
            [
                message
                for message in self._messages.values()
                if message.tenant_id == tenant_id and message.conversation_id == conversation_id
            ],
            key=lambda item: (item.created_at, item.id),
        )

    async def list_recent_chat(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        limit: int,
        exclude_message_id: UUID | None = None,
    ) -> list[Message]:
        messages = await self.list_by_conversation(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
        )
        if exclude_message_id is not None:
            messages = [message for message in messages if message.id != exclude_message_id]
        return messages[-limit:]


class InMemoryRunTriggerRepository(RunTriggerRepository):
    def __init__(self) -> None:
        self.triggers: list[RunTrigger] = []

    async def add(self, trigger: RunTrigger) -> RunTrigger:
        self.triggers.append(trigger)
        return trigger


def build_conversation(*, tenant_id: UUID, project_id: UUID, title: str) -> Conversation:
    timestamp = datetime.now(tz=UTC)
    return Conversation.create(
        id=uuid4(),
        tenant_id=tenant_id,
        project_id=project_id,
        created_by_user_id=uuid4(),
        title=title,
        created_at=timestamp,
        updated_at=timestamp,
    )


def with_created_at(conversation: Conversation, created_at: datetime) -> Conversation:
    return replace(conversation, created_at=created_at)


def _conversation_sort_key(conversation: Conversation) -> tuple[datetime, UUID]:
    return conversation.last_message_at or conversation.created_at, conversation.id
