import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from researchlens.modules.conversations.application.dto import (
    RunTriggerView,
    to_run_trigger_view,
)
from researchlens.modules.conversations.application.ports import (
    ConversationRepository,
    MessageRepository,
    RunTriggerRepository,
    TransactionManager,
)
from researchlens.modules.conversations.domain import RunTrigger
from researchlens.shared.errors import NotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RecordRunTriggerCommand:
    tenant_id: UUID
    user_id: UUID
    conversation_id: UUID
    source_message_id: UUID | None
    request_text: str
    client_request_id: str | None


class RecordRunTriggerUseCase:
    def __init__(
        self,
        *,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
        run_trigger_repository: RunTriggerRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._run_trigger_repository = run_trigger_repository
        self._transaction_manager = transaction_manager

    async def execute(self, command: RecordRunTriggerCommand) -> RunTriggerView:
        async with self._transaction_manager.boundary():
            conversation = await self._conversation_repository.get_by_id_for_tenant(
                tenant_id=command.tenant_id,
                conversation_id=command.conversation_id,
            )
            if conversation is None:
                raise NotFoundError("Conversation was not found.")

            if command.source_message_id is not None:
                message = await self._message_repository.get_by_id_for_tenant(
                    tenant_id=command.tenant_id,
                    conversation_id=command.conversation_id,
                    message_id=command.source_message_id,
                )
                if message is None:
                    raise NotFoundError("Message was not found.")

            trigger = RunTrigger.create(
                id=uuid4(),
                tenant_id=command.tenant_id,
                conversation_id=command.conversation_id,
                project_id=conversation.project_id,
                source_message_id=command.source_message_id,
                request_text=command.request_text,
                client_request_id=command.client_request_id,
                created_by_user_id=command.user_id,
                created_at=datetime.now(tz=UTC),
            )
            created_trigger = await self._run_trigger_repository.add(trigger)

        logger.info(
            "conversation.run_trigger.record tenant_id=%s user_id=%s project_id=%s "
            "conversation_id=%s source_message_id=%s trigger_id=%s",
            command.tenant_id,
            command.user_id,
            conversation.project_id,
            command.conversation_id,
            command.source_message_id,
            created_trigger.id,
        )
        return to_run_trigger_view(created_trigger)
