from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from researchlens.modules.conversations.application import (
    CreateConversationCommand,
    CreateConversationUseCase,
    GetConversationQuery,
    GetConversationUseCase,
    ListConversationsQuery,
    ListConversationsUseCase,
    PostMessageCommand,
    PostMessageUseCase,
    RecordRunTriggerCommand,
    RecordRunTriggerUseCase,
)
from researchlens.modules.conversations.application.cursor import (
    ConversationListCursor,
    decode_conversation_cursor,
)
from researchlens.modules.conversations.application.ports import (
    ConversationRepository,
    MessageRepository,
    ProjectScopeReader,
    RunTriggerRepository,
)
from researchlens.modules.conversations.domain import (
    Conversation,
    Message,
    MessageRole,
    MessageType,
    RunTrigger,
)
from researchlens.shared.errors import NotFoundError


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
        items.sort(
            key=lambda item: (
                item.last_message_at or item.created_at,
                item.id,
            ),
            reverse=True,
        )
        if cursor is not None:
            items = [
                item
                for item in items
                if (item.last_message_at or item.created_at, item.id)
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


@pytest.mark.asyncio
async def test_create_conversation_requires_existing_project() -> None:
    use_case = CreateConversationUseCase(
        conversation_repository=InMemoryConversationRepository(),
        project_scope_reader=InMemoryProjectScopeReader(set()),
        transaction_manager=FakeTransactionManager(),
    )

    with pytest.raises(NotFoundError):
        await use_case.execute(
            CreateConversationCommand(
                tenant_id=uuid4(),
                user_id=uuid4(),
                project_id=uuid4(),
                title="Alpha",
            )
        )


@pytest.mark.asyncio
async def test_list_conversations_returns_cursor_for_next_page() -> None:
    tenant_id = uuid4()
    project_id = uuid4()
    first = build_conversation(tenant_id=tenant_id, project_id=project_id, title="First")
    second = replace(
        build_conversation(tenant_id=tenant_id, project_id=project_id, title="Second"),
        created_at=first.created_at.replace(microsecond=0),
    )
    repository = InMemoryConversationRepository([first, second])
    use_case = ListConversationsUseCase(
        conversation_repository=repository,
        project_scope_reader=InMemoryProjectScopeReader({project_id}),
    )

    page = await use_case.execute(
        ListConversationsQuery(
            tenant_id=tenant_id,
            user_id=uuid4(),
            project_id=project_id,
            cursor=None,
            limit=1,
        )
    )

    assert len(page.items) == 1
    assert page.next_cursor is not None
    assert decode_conversation_cursor(page.next_cursor).conversation_id == page.items[0].id


@pytest.mark.asyncio
async def test_post_message_replays_idempotent_message() -> None:
    tenant_id = uuid4()
    project_id = uuid4()
    conversation = build_conversation(tenant_id=tenant_id, project_id=project_id, title="Alpha")
    message = Message.create(
        id=uuid4(),
        tenant_id=tenant_id,
        conversation_id=conversation.id,
        role=MessageRole.USER,
        type=MessageType.TEXT,
        content_text="hello",
        content_json=None,
        metadata_json=None,
        created_at=datetime.now(tz=UTC),
        client_message_id="msg-1",
    )
    use_case = PostMessageUseCase(
        conversation_repository=InMemoryConversationRepository([conversation]),
        message_repository=InMemoryMessageRepository([message]),
        transaction_manager=FakeTransactionManager(),
    )

    result = await use_case.execute(
        PostMessageCommand(
            tenant_id=tenant_id,
            user_id=uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.USER,
            type=MessageType.TEXT,
            content_text="hello",
            content_json=None,
            metadata_json=None,
            client_message_id="msg-1",
        )
    )

    assert result.idempotent_replay is True
    assert result.message.id == message.id


@pytest.mark.asyncio
async def test_record_run_trigger_requires_existing_source_message() -> None:
    tenant_id = uuid4()
    project_id = uuid4()
    conversation = build_conversation(tenant_id=tenant_id, project_id=project_id, title="Alpha")
    use_case = RecordRunTriggerUseCase(
        conversation_repository=InMemoryConversationRepository([conversation]),
        message_repository=InMemoryMessageRepository(),
        run_trigger_repository=InMemoryRunTriggerRepository(),
        transaction_manager=FakeTransactionManager(),
    )

    with pytest.raises(NotFoundError):
        await use_case.execute(
            RecordRunTriggerCommand(
                tenant_id=tenant_id,
                user_id=uuid4(),
                conversation_id=conversation.id,
                source_message_id=uuid4(),
                request_text="Run this conversation",
                client_request_id="request-1",
            )
        )


@pytest.mark.asyncio
async def test_get_conversation_returns_scoped_conversation() -> None:
    tenant_id = uuid4()
    conversation = build_conversation(tenant_id=tenant_id, project_id=uuid4(), title="Alpha")
    use_case = GetConversationUseCase(
        conversation_repository=InMemoryConversationRepository([conversation]),
    )

    view = await use_case.execute(
        GetConversationQuery(
            tenant_id=tenant_id,
            user_id=uuid4(),
            conversation_id=conversation.id,
        )
    )

    assert view.id == conversation.id
    assert view.title == "Alpha"
