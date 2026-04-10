import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from researchlens.modules.conversations.application.dto import (
    ConversationView,
    to_conversation_view,
)
from researchlens.modules.conversations.application.ports import (
    ConversationRepository,
    TransactionManager,
)
from researchlens.shared.errors import NotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class UpdateConversationCommand:
    tenant_id: UUID
    user_id: UUID
    conversation_id: UUID
    title: str


class UpdateConversationUseCase:
    def __init__(
        self,
        *,
        conversation_repository: ConversationRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._transaction_manager = transaction_manager

    async def execute(self, command: UpdateConversationCommand) -> ConversationView:
        async with self._transaction_manager.boundary():
            conversation = await self._conversation_repository.get_by_id_for_tenant(
                tenant_id=command.tenant_id,
                conversation_id=command.conversation_id,
            )
            if conversation is None:
                raise NotFoundError("Conversation was not found.")

            updated_conversation = conversation.update_title(
                title=command.title,
                updated_at=datetime.now(tz=UTC),
            )
            saved_conversation = await self._conversation_repository.save(updated_conversation)
            if saved_conversation is None:
                raise NotFoundError("Conversation was not found.")

        logger.info(
            "conversation.update tenant_id=%s user_id=%s conversation_id=%s",
            command.tenant_id,
            command.user_id,
            command.conversation_id,
        )
        return to_conversation_view(saved_conversation)
