import logging
from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.conversations.application.dto import MessageView, to_message_view
from researchlens.modules.conversations.application.ports import (
    ConversationRepository,
    MessageRepository,
)
from researchlens.shared.errors import NotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ListMessagesQuery:
    tenant_id: UUID
    user_id: UUID
    conversation_id: UUID


class ListMessagesUseCase:
    def __init__(
        self,
        *,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository

    async def execute(self, query: ListMessagesQuery) -> list[MessageView]:
        conversation = await self._conversation_repository.get_by_id_for_tenant(
            tenant_id=query.tenant_id,
            conversation_id=query.conversation_id,
        )
        if conversation is None:
            raise NotFoundError("Conversation was not found.")

        messages = await self._message_repository.list_by_conversation(
            tenant_id=query.tenant_id,
            conversation_id=query.conversation_id,
        )
        logger.info(
            "message.list tenant_id=%s user_id=%s conversation_id=%s count=%s",
            query.tenant_id,
            query.user_id,
            query.conversation_id,
            len(messages),
        )
        return [to_message_view(message) for message in messages]
