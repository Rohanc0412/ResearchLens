from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from researchlens.modules.conversations.application import (
    CreateConversationUseCase,
    DeleteConversationUseCase,
    GetConversationUseCase,
    GetMessageUseCase,
    ListConversationsUseCase,
    ListMessagesUseCase,
    PostMessageUseCase,
    RecordRunTriggerUseCase,
    UpdateConversationUseCase,
)
from researchlens.modules.conversations.infrastructure.conversation_repository_sql import (
    SqlAlchemyConversationRepository,
)
from researchlens.modules.conversations.infrastructure.message_repository_sql import (
    SqlAlchemyMessageRepository,
)
from researchlens.modules.conversations.infrastructure.project_scope_reader_sql import (
    SqlAlchemyProjectScopeReader,
)
from researchlens.modules.conversations.infrastructure.run_trigger_repository_sql import (
    SqlAlchemyRunTriggerRepository,
)
from researchlens.shared.db import SqlAlchemyTransactionManager


@dataclass(slots=True)
class ConversationsRequestContext:
    create_conversation: CreateConversationUseCase
    list_conversations: ListConversationsUseCase
    get_conversation: GetConversationUseCase
    update_conversation: UpdateConversationUseCase
    delete_conversation: DeleteConversationUseCase
    post_message: PostMessageUseCase
    list_messages: ListMessagesUseCase
    get_message: GetMessageUseCase
    record_run_trigger: RecordRunTriggerUseCase


class SqlAlchemyConversationsRuntime:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @asynccontextmanager
    async def request_context(self) -> AsyncIterator[ConversationsRequestContext]:
        async with self._session_factory() as session:
            yield self._build_context(session)

    def _build_context(self, session: AsyncSession) -> ConversationsRequestContext:
        conversation_repository = SqlAlchemyConversationRepository(session)
        message_repository = SqlAlchemyMessageRepository(session)
        project_scope_reader = SqlAlchemyProjectScopeReader(session)
        run_trigger_repository = SqlAlchemyRunTriggerRepository(session)
        transaction_manager = SqlAlchemyTransactionManager(session)
        return ConversationsRequestContext(
            create_conversation=CreateConversationUseCase(
                conversation_repository=conversation_repository,
                project_scope_reader=project_scope_reader,
                transaction_manager=transaction_manager,
            ),
            list_conversations=ListConversationsUseCase(
                conversation_repository=conversation_repository,
                project_scope_reader=project_scope_reader,
            ),
            get_conversation=GetConversationUseCase(
                conversation_repository=conversation_repository,
            ),
            update_conversation=UpdateConversationUseCase(
                conversation_repository=conversation_repository,
                transaction_manager=transaction_manager,
            ),
            delete_conversation=DeleteConversationUseCase(
                conversation_repository=conversation_repository,
                transaction_manager=transaction_manager,
            ),
            post_message=PostMessageUseCase(
                conversation_repository=conversation_repository,
                message_repository=message_repository,
                transaction_manager=transaction_manager,
            ),
            list_messages=ListMessagesUseCase(
                conversation_repository=conversation_repository,
                message_repository=message_repository,
            ),
            get_message=GetMessageUseCase(
                conversation_repository=conversation_repository,
                message_repository=message_repository,
            ),
            record_run_trigger=RecordRunTriggerUseCase(
                conversation_repository=conversation_repository,
                message_repository=message_repository,
                run_trigger_repository=run_trigger_repository,
                transaction_manager=transaction_manager,
            ),
        )
