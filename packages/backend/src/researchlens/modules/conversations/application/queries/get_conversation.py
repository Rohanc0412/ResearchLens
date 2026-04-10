import logging
from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.conversations.application.dto import (
    ConversationView,
    to_conversation_view,
)
from researchlens.modules.conversations.application.ports import ConversationRepository
from researchlens.shared.errors import NotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GetConversationQuery:
    tenant_id: UUID
    user_id: UUID
    conversation_id: UUID


class GetConversationUseCase:
    def __init__(self, *, conversation_repository: ConversationRepository) -> None:
        self._conversation_repository = conversation_repository

    async def execute(self, query: GetConversationQuery) -> ConversationView:
        conversation = await self._conversation_repository.get_by_id_for_tenant(
            tenant_id=query.tenant_id,
            conversation_id=query.conversation_id,
        )
        if conversation is None:
            raise NotFoundError("Conversation was not found.")
        logger.info(
            "conversation.get tenant_id=%s user_id=%s conversation_id=%s",
            query.tenant_id,
            query.user_id,
            query.conversation_id,
        )
        return to_conversation_view(conversation)
