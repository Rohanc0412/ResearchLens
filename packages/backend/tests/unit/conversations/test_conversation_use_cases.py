from datetime import UTC, datetime
from uuid import uuid4

import pytest
from packages.backend.tests.unit.conversations.fakes import (
    FakeTransactionManager,
    InMemoryConversationRepository,
    InMemoryMessageRepository,
    InMemoryProjectScopeReader,
    InMemoryRunTriggerRepository,
    build_conversation,
    with_created_at,
)

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
    decode_conversation_cursor,
)
from researchlens.modules.conversations.domain import (
    Message,
    MessageRole,
    MessageType,
)
from researchlens.shared.errors import NotFoundError


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
    second = with_created_at(
        build_conversation(tenant_id=tenant_id, project_id=project_id, title="Second"),
        first.created_at.replace(microsecond=0),
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
