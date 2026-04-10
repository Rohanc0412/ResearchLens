from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.conversations.application.ports import MessageRepository
from researchlens.modules.conversations.domain import Message
from researchlens.modules.conversations.infrastructure.mappers import to_message_domain
from researchlens.modules.conversations.infrastructure.rows.message_row import MessageRow


class SqlAlchemyMessageRepository(MessageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, message: Message) -> Message:
        row = MessageRow(
            id=message.id,
            tenant_id=message.tenant_id,
            conversation_id=message.conversation_id,
            role=message.role.value,
            type=message.type.value,
            content_text=message.content_text,
            content_json=message.content_json,
            metadata_json=message.metadata_json,
            created_at=message.created_at,
            client_message_id=message.client_message_id,
        )
        self._session.add(row)
        await self._session.flush()
        return to_message_domain(row)

    async def get_by_id_for_tenant(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
    ) -> Message | None:
        statement = select(MessageRow).where(
            MessageRow.tenant_id == tenant_id,
            MessageRow.conversation_id == conversation_id,
            MessageRow.id == message_id,
        )
        row = await self._session.scalar(statement)
        if row is None:
            return None
        return to_message_domain(row)

    async def get_by_client_message_id(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        client_message_id: str,
    ) -> Message | None:
        statement = select(MessageRow).where(
            MessageRow.tenant_id == tenant_id,
            MessageRow.conversation_id == conversation_id,
            MessageRow.client_message_id == client_message_id,
        )
        row = await self._session.scalar(statement)
        if row is None:
            return None
        return to_message_domain(row)

    async def list_by_conversation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
    ) -> list[Message]:
        statement = (
            select(MessageRow)
            .where(
                MessageRow.tenant_id == tenant_id,
                MessageRow.conversation_id == conversation_id,
            )
            .order_by(MessageRow.created_at.asc(), MessageRow.id.asc())
        )
        rows = await self._session.scalars(statement)
        return [to_message_domain(row) for row in rows]
