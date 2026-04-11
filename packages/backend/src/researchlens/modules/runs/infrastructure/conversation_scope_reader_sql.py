from uuid import UUID

from sqlalchemy import column, select, table
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Uuid

from researchlens.modules.runs.application.ports import (
    ConversationRunSource,
    ConversationScopeReader,
)

conversations_table = table(
    "conversations",
    column("id", Uuid),
    column("tenant_id", Uuid),
    column("project_id", Uuid),
)


class SqlAlchemyConversationScopeReader(ConversationScopeReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_conversation_source(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
    ) -> ConversationRunSource | None:
        statement = select(
            conversations_table.c.id,
            conversations_table.c.project_id,
        ).where(
            conversations_table.c.tenant_id == tenant_id,
            conversations_table.c.id == conversation_id,
        )
        row = (await self._session.execute(statement)).one_or_none()
        if row is None:
            return None
        return ConversationRunSource(
            conversation_id=row.id,
            project_id=row.project_id,
        )
