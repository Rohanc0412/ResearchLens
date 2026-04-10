from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.conversations.application.cursor import ConversationListCursor
from researchlens.modules.conversations.application.ports import ConversationRepository
from researchlens.modules.conversations.domain import Conversation
from researchlens.modules.conversations.infrastructure.mappers import (
    to_conversation_domain,
    update_conversation_row,
)
from researchlens.modules.conversations.infrastructure.rows.conversation_row import (
    ConversationRow,
)


class SqlAlchemyConversationRepository(ConversationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, conversation: Conversation) -> Conversation:
        row = ConversationRow(
            id=conversation.id,
            tenant_id=conversation.tenant_id,
            project_id=conversation.project_id,
            created_by_user_id=conversation.created_by_user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            last_message_at=conversation.last_message_at,
        )
        self._session.add(row)
        await self._session.flush()
        return to_conversation_domain(row)

    async def get_by_id_for_tenant(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
    ) -> Conversation | None:
        statement = select(ConversationRow).where(
            ConversationRow.tenant_id == tenant_id,
            ConversationRow.id == conversation_id,
        )
        row = await self._session.scalar(statement)
        if row is None:
            return None
        return to_conversation_domain(row)

    async def list_by_project(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
        limit: int,
        cursor: ConversationListCursor | None,
    ) -> list[Conversation]:
        activity_expr = func.coalesce(
            ConversationRow.last_message_at,
            ConversationRow.created_at,
        )
        statement = (
            select(ConversationRow)
            .where(
                ConversationRow.tenant_id == tenant_id,
                ConversationRow.project_id == project_id,
            )
            .order_by(activity_expr.desc(), ConversationRow.id.desc())
            .limit(limit)
        )
        if cursor is not None:
            statement = statement.where(
                or_(
                    activity_expr < cursor.activity_at,
                    (activity_expr == cursor.activity_at)
                    & (ConversationRow.id < cursor.conversation_id),
                )
            )
        rows = await self._session.scalars(statement)
        return [to_conversation_domain(row) for row in rows]

    async def save(self, conversation: Conversation) -> Conversation | None:
        statement = select(ConversationRow).where(
            ConversationRow.tenant_id == conversation.tenant_id,
            ConversationRow.id == conversation.id,
        )
        row = await self._session.scalar(statement)
        if row is None:
            return None
        update_conversation_row(row, conversation)
        await self._session.flush()
        return to_conversation_domain(row)

    async def delete_by_id_for_tenant(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
    ) -> bool:
        statement = delete(ConversationRow).where(
            ConversationRow.tenant_id == tenant_id,
            ConversationRow.id == conversation_id,
        )
        result = await self._session.execute(statement)
        return bool(getattr(result, "rowcount", 0))
