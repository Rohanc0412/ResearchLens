from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.conversations.application.ports import RunTriggerRepository
from researchlens.modules.conversations.domain import RunTrigger
from researchlens.modules.conversations.infrastructure.mappers import to_run_trigger_domain
from researchlens.modules.conversations.infrastructure.rows.run_trigger_row import (
    RunTriggerRow,
)


class SqlAlchemyRunTriggerRepository(RunTriggerRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, trigger: RunTrigger) -> RunTrigger:
        row = RunTriggerRow(
            id=trigger.id,
            tenant_id=trigger.tenant_id,
            conversation_id=trigger.conversation_id,
            project_id=trigger.project_id,
            source_message_id=trigger.source_message_id,
            request_text=trigger.request_text,
            client_request_id=trigger.client_request_id,
            status=trigger.status.value,
            created_by_user_id=trigger.created_by_user_id,
            created_at=trigger.created_at,
        )
        self._session.add(row)
        await self._session.flush()
        return to_run_trigger_domain(row)
