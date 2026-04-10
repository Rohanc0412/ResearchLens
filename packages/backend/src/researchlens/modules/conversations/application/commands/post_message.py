import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from researchlens.modules.conversations.application.dto import (
    MessageWriteResult,
    to_message_view,
)
from researchlens.modules.conversations.application.ports import (
    ConversationRepository,
    MessageRepository,
    TransactionManager,
)
from researchlens.modules.conversations.domain import Message, MessageRole, MessageType
from researchlens.shared.errors import NotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PostMessageCommand:
    tenant_id: UUID
    user_id: UUID
    conversation_id: UUID
    role: MessageRole
    type: MessageType
    content_text: str | None
    content_json: dict[str, Any] | list[Any] | None
    metadata_json: dict[str, Any] | None
    client_message_id: str | None


class PostMessageUseCase:
    def __init__(
        self,
        *,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._transaction_manager = transaction_manager

    async def execute(self, command: PostMessageCommand) -> MessageWriteResult:
        async with self._transaction_manager.boundary():
            conversation = await self._conversation_repository.get_by_id_for_tenant(
                tenant_id=command.tenant_id,
                conversation_id=command.conversation_id,
            )
            if conversation is None:
                raise NotFoundError("Conversation was not found.")

            if command.client_message_id is not None:
                existing_message = await self._message_repository.get_by_client_message_id(
                    tenant_id=command.tenant_id,
                    conversation_id=command.conversation_id,
                    client_message_id=command.client_message_id,
                )
                if existing_message is not None:
                    logger.info(
                        "message.create tenant_id=%s user_id=%s conversation_id=%s "
                        "message_id=%s client_message_id=%s replay=true",
                        command.tenant_id,
                        command.user_id,
                        command.conversation_id,
                        existing_message.id,
                        existing_message.client_message_id,
                    )
                    return MessageWriteResult(
                        message=to_message_view(existing_message),
                        idempotent_replay=True,
                    )

            timestamp = datetime.now(tz=UTC)
            message = Message.create(
                id=uuid4(),
                tenant_id=command.tenant_id,
                conversation_id=command.conversation_id,
                role=command.role,
                type=command.type,
                content_text=command.content_text,
                content_json=command.content_json,
                metadata_json=command.metadata_json,
                created_at=timestamp,
                client_message_id=command.client_message_id,
            )
            created_message = await self._message_repository.add(message)
            updated_conversation = conversation.record_message(
                message_created_at=created_message.created_at
            )
            await self._conversation_repository.save(updated_conversation)

        logger.info(
            "message.create tenant_id=%s user_id=%s conversation_id=%s message_id=%s "
            "client_message_id=%s replay=false",
            command.tenant_id,
            command.user_id,
            command.conversation_id,
            created_message.id,
            created_message.client_message_id,
        )
        return MessageWriteResult(
            message=to_message_view(created_message),
            idempotent_replay=False,
        )
