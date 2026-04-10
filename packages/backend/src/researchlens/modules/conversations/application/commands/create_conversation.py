import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from researchlens.modules.conversations.application.dto import (
    ConversationView,
    to_conversation_view,
)
from researchlens.modules.conversations.application.ports import (
    ConversationRepository,
    ProjectScopeReader,
    TransactionManager,
)
from researchlens.modules.conversations.domain import Conversation
from researchlens.shared.errors import NotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CreateConversationCommand:
    tenant_id: UUID
    user_id: UUID
    project_id: UUID
    title: str


class CreateConversationUseCase:
    def __init__(
        self,
        *,
        conversation_repository: ConversationRepository,
        project_scope_reader: ProjectScopeReader,
        transaction_manager: TransactionManager,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._project_scope_reader = project_scope_reader
        self._transaction_manager = transaction_manager

    async def execute(self, command: CreateConversationCommand) -> ConversationView:
        async with self._transaction_manager.boundary():
            project_exists = await self._project_scope_reader.project_exists_for_tenant(
                tenant_id=command.tenant_id,
                project_id=command.project_id,
            )
            if not project_exists:
                raise NotFoundError("Project was not found.")

            timestamp = datetime.now(tz=UTC)
            conversation = Conversation.create(
                id=uuid4(),
                tenant_id=command.tenant_id,
                project_id=command.project_id,
                created_by_user_id=command.user_id,
                title=command.title,
                created_at=timestamp,
                updated_at=timestamp,
            )
            created_conversation = await self._conversation_repository.add(conversation)

        logger.info(
            "conversation.create tenant_id=%s user_id=%s project_id=%s conversation_id=%s",
            command.tenant_id,
            command.user_id,
            command.project_id,
            created_conversation.id,
        )
        return to_conversation_view(created_conversation)
