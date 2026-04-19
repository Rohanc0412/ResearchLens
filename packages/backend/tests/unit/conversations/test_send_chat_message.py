from uuid import uuid4

import pytest

from researchlens.modules.conversations.application import (
    SendChatMessageCommand,
    SendChatMessageUseCase,
)

from .fakes import (
    FakeTransactionManager,
    InMemoryConversationRepository,
    InMemoryMessageRepository,
    build_conversation,
)


@pytest.mark.asyncio
async def test_research_style_prompt_only_offers_pipeline() -> None:
    tenant_id = uuid4()
    project_id = uuid4()
    conversation = build_conversation(
        tenant_id=tenant_id,
        project_id=project_id,
        title="Research",
    )
    use_case = SendChatMessageUseCase(
        conversation_repository=InMemoryConversationRepository([conversation]),
        message_repository=InMemoryMessageRepository(),
        transaction_manager=FakeTransactionManager(),
    )

    result = await use_case.execute(
        SendChatMessageCommand(
            tenant_id=tenant_id,
            user_id=uuid4(),
            conversation_id=conversation.id,
            message="Write a literature review with citations about cancer biomarkers.",
            client_message_id="chat-1",
        )
    )

    assert result.kind == "immediate"
    assert result.assistant_message is not None
    assert result.assistant_message.type == "pipeline_offer"
    assert result.pending_action is not None
    assert result.pending_action["type"] == "research_run_offer"


@pytest.mark.asyncio
async def test_force_pipeline_returns_run_start_payload() -> None:
    tenant_id = uuid4()
    project_id = uuid4()
    conversation = build_conversation(
        tenant_id=tenant_id,
        project_id=project_id,
        title="Research",
    )
    use_case = SendChatMessageUseCase(
        conversation_repository=InMemoryConversationRepository([conversation]),
        message_repository=InMemoryMessageRepository(),
        transaction_manager=FakeTransactionManager(),
    )

    result = await use_case.execute(
        SendChatMessageCommand(
            tenant_id=tenant_id,
            user_id=uuid4(),
            conversation_id=conversation.id,
            message="Compare foundation models for scientific search.",
            client_message_id="chat-2",
            force_pipeline=True,
        )
    )

    assert result.kind == "immediate"
    assert result.assistant_message is not None
    assert result.assistant_message.type == "run_started"
    assert result.pending_action == {
        "type": "start_research_run",
        "prompt": "Compare foundation models for scientific search.",
    }


@pytest.mark.asyncio
async def test_force_pipeline_idempotent_replay_keeps_run_start_payload() -> None:
    tenant_id = uuid4()
    project_id = uuid4()
    conversation = build_conversation(
        tenant_id=tenant_id,
        project_id=project_id,
        title="Research",
    )
    message_repository = InMemoryMessageRepository()
    use_case = SendChatMessageUseCase(
        conversation_repository=InMemoryConversationRepository([conversation]),
        message_repository=message_repository,
        transaction_manager=FakeTransactionManager(),
    )
    command = SendChatMessageCommand(
        tenant_id=tenant_id,
        user_id=uuid4(),
        conversation_id=conversation.id,
        message="Summarize protein folding benchmarks.",
        client_message_id="chat-3",
        force_pipeline=True,
    )

    first_result = await use_case.execute(command)
    replay_result = await use_case.execute(command)

    assert first_result.kind == "immediate"
    assert replay_result.kind == "immediate"
    assert replay_result.idempotent_replay is True
    assert replay_result.assistant_message is not None
    assert replay_result.assistant_message.type == "run_started"
    assert replay_result.pending_action == {
        "type": "start_research_run",
        "prompt": "Summarize protein folding benchmarks.",
    }


@pytest.mark.asyncio
async def test_run_pipeline_action_returns_run_start_payload() -> None:
    tenant_id = uuid4()
    project_id = uuid4()
    conversation = build_conversation(
        tenant_id=tenant_id,
        project_id=project_id,
        title="Research",
    )
    use_case = SendChatMessageUseCase(
        conversation_repository=InMemoryConversationRepository([conversation]),
        message_repository=InMemoryMessageRepository(),
        transaction_manager=FakeTransactionManager(),
    )

    await use_case.execute(
        SendChatMessageCommand(
            tenant_id=tenant_id,
            user_id=uuid4(),
            conversation_id=conversation.id,
            message="Write a literature review with citations about cancer biomarkers.",
            client_message_id="chat-offer",
        )
    )
    result = await use_case.execute(
        SendChatMessageCommand(
            tenant_id=tenant_id,
            user_id=uuid4(),
            conversation_id=conversation.id,
            message="__ACTION__:run_pipeline",
            client_message_id="chat-run",
        )
    )

    assert result.kind == "immediate"
    assert result.assistant_message is not None
    assert result.assistant_message.type == "run_started"
    assert result.pending_action == {
        "type": "start_research_run",
        "prompt": "Write a literature review with citations about cancer biomarkers.",
    }


@pytest.mark.asyncio
async def test_confirmed_consent_reply_keeps_pipeline_offer() -> None:
    tenant_id = uuid4()
    project_id = uuid4()
    conversation = build_conversation(
        tenant_id=tenant_id,
        project_id=project_id,
        title="Research",
    )
    use_case = SendChatMessageUseCase(
        conversation_repository=InMemoryConversationRepository([conversation]),
        message_repository=InMemoryMessageRepository(),
        transaction_manager=FakeTransactionManager(),
    )

    await use_case.execute(
        SendChatMessageCommand(
            tenant_id=tenant_id,
            user_id=uuid4(),
            conversation_id=conversation.id,
            message="Write a literature review with citations about cancer biomarkers.",
            client_message_id="chat-offer",
        )
    )
    result = await use_case.execute(
        SendChatMessageCommand(
            tenant_id=tenant_id,
            user_id=uuid4(),
            conversation_id=conversation.id,
            message="yes",
            client_message_id="chat-consent",
        )
    )

    assert result.kind == "immediate"
    assert result.assistant_message is not None
    assert result.assistant_message.type == "pipeline_offer"
    assert result.pending_action is not None
    assert result.pending_action["type"] == "research_run_offer"
    assert result.pending_action["prompt"] == (
        "Write a literature review with citations about cancer biomarkers."
    )


@pytest.mark.asyncio
async def test_greeting_links_assistant_reply_without_reinserting_user_message() -> None:
    tenant_id = uuid4()
    project_id = uuid4()
    conversation = build_conversation(
        tenant_id=tenant_id,
        project_id=project_id,
        title="Greeting",
    )
    message_repository = InMemoryMessageRepository()
    use_case = SendChatMessageUseCase(
        conversation_repository=InMemoryConversationRepository([conversation]),
        message_repository=message_repository,
        transaction_manager=FakeTransactionManager(),
    )

    result = await use_case.execute(
        SendChatMessageCommand(
            tenant_id=tenant_id,
            user_id=uuid4(),
            conversation_id=conversation.id,
            message="hello",
            client_message_id="chat-greeting",
        )
    )

    assert result.kind == "immediate"
    assert result.assistant_message is not None
    messages = await message_repository.list_by_conversation(
        tenant_id=tenant_id,
        conversation_id=conversation.id,
    )
    assert len(messages) == 2
    assert messages[0].metadata_json == {
        "reply_message_id": str(result.assistant_message.id),
    }
