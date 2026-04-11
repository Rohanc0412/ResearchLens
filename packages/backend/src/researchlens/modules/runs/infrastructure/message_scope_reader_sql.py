from uuid import UUID

from sqlalchemy import column, select, table
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Uuid

from researchlens.modules.runs.application.ports import MessageScopeReader

messages_table = table(
    "messages",
    column("id", Uuid),
    column("tenant_id", Uuid),
    column("conversation_id", Uuid),
)


class SqlAlchemyMessageScopeReader(MessageScopeReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def message_exists_for_conversation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
    ) -> bool:
        statement = select(messages_table.c.id).where(
            messages_table.c.tenant_id == tenant_id,
            messages_table.c.conversation_id == conversation_id,
            messages_table.c.id == message_id,
        )
        return await self._session.scalar(statement) is not None
