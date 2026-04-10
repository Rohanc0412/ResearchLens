import logging
from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.conversations.application.ports import (
    ConversationRepository,
    TransactionManager,
)
from researchlens.shared.errors import NotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DeleteConversationCommand:
    tenant_id: UUID
    user_id: UUID
    conversation_id: UUID


class DeleteConversationUseCase:
    def __init__(
        self,
        *,
        conversation_repository: ConversationRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._transaction_manager = transaction_manager

    async def execute(self, command: DeleteConversationCommand) -> None:
        async with self._transaction_manager.boundary():
            deleted = await self._conversation_repository.delete_by_id_for_tenant(
                tenant_id=command.tenant_id,
                conversation_id=command.conversation_id,
            )
            if not deleted:
                raise NotFoundError("Conversation was not found.")

        logger.info(
            "conversation.delete tenant_id=%s user_id=%s conversation_id=%s",
            command.tenant_id,
            command.user_id,
            command.conversation_id,
        )
