import logging
from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.conversations.application.cursor import decode_conversation_cursor
from researchlens.modules.conversations.application.dto import (
    ConversationListPage,
    to_conversation_list_page,
)
from researchlens.modules.conversations.application.ports import (
    ConversationRepository,
    ProjectScopeReader,
)
from researchlens.shared.errors import NotFoundError, ValidationError

logger = logging.getLogger(__name__)
DEFAULT_LIST_LIMIT = 20
MAX_LIST_LIMIT = 100


@dataclass(frozen=True, slots=True)
class ListConversationsQuery:
    tenant_id: UUID
    user_id: UUID
    project_id: UUID
    cursor: str | None
    limit: int = DEFAULT_LIST_LIMIT


class ListConversationsUseCase:
    def __init__(
        self,
        *,
        conversation_repository: ConversationRepository,
        project_scope_reader: ProjectScopeReader,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._project_scope_reader = project_scope_reader

    async def execute(self, query: ListConversationsQuery) -> ConversationListPage:
        if query.limit < 1 or query.limit > MAX_LIST_LIMIT:
            raise ValidationError("Conversation list limit must be between 1 and 100.")

        project_exists = await self._project_scope_reader.project_exists_for_tenant(
            tenant_id=query.tenant_id,
            project_id=query.project_id,
        )
        if not project_exists:
            raise NotFoundError("Project was not found.")

        cursor = None if query.cursor is None else decode_conversation_cursor(query.cursor)
        conversations = await self._conversation_repository.list_by_project(
            tenant_id=query.tenant_id,
            project_id=query.project_id,
            limit=query.limit + 1,
            cursor=cursor,
        )
        has_more = len(conversations) > query.limit
        page_items = conversations[: query.limit]
        page = to_conversation_list_page(page_items)
        if not has_more:
            page = ConversationListPage(items=page.items, next_cursor=None)

        logger.info(
            "conversation.list tenant_id=%s user_id=%s project_id=%s count=%s",
            query.tenant_id,
            query.user_id,
            query.project_id,
            len(page.items),
        )
        return page
