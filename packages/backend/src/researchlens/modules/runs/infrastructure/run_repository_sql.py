from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.runs.application.ports import RunRepository
from researchlens.modules.runs.domain import Run, RunTransitionRecord
from researchlens.modules.runs.infrastructure.mappers import (
    to_run_domain,
    to_transition_domain,
    update_run_row,
)
from researchlens.modules.runs.infrastructure.rows import RunRow, RunTransitionRow


class SqlAlchemyRunRepository(RunRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, run: Run) -> Run:
        row = RunRow(
            id=run.id,
            tenant_id=run.tenant_id,
            project_id=run.project_id,
            conversation_id=run.conversation_id,
            created_by_user_id=run.created_by_user_id,
            status=run.status.value,
            current_stage=run.current_stage.value if run.current_stage else None,
            output_type=run.output_type,
            trigger_message_id=run.trigger_message_id,
            client_request_id=run.client_request_id,
            cancel_requested_at=run.cancel_requested_at,
            started_at=run.started_at,
            finished_at=run.finished_at,
            retry_count=run.retry_count,
            failure_reason=run.failure_reason,
            error_code=run.error_code,
            last_event_number=run.last_event_number,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )
        self._session.add(row)
        await self._session.flush()
        return to_run_domain(row)

    async def get_by_id_for_tenant(self, *, tenant_id: UUID, run_id: UUID) -> Run | None:
        statement = select(RunRow).where(
            RunRow.tenant_id == tenant_id,
            RunRow.id == run_id,
        )
        row = await self._session.scalar(statement)
        return to_run_domain(row) if row is not None else None

    async def get_by_id(self, *, run_id: UUID) -> Run | None:
        row = await self._session.get(RunRow, run_id)
        return to_run_domain(row) if row is not None else None

    async def get_by_id_for_update(self, *, run_id: UUID) -> Run | None:
        statement = select(RunRow).where(RunRow.id == run_id).with_for_update()
        row = await self._session.scalar(statement)
        return to_run_domain(row) if row is not None else None

    async def get_by_client_request_id(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        client_request_id: str,
    ) -> Run | None:
        statement = select(RunRow).where(
            RunRow.tenant_id == tenant_id,
            RunRow.conversation_id == conversation_id,
            RunRow.client_request_id == client_request_id,
        )
        row = await self._session.scalar(statement)
        return to_run_domain(row) if row is not None else None

    async def save(self, run: Run) -> Run:
        row = await self._session.get(RunRow, run.id)
        if row is None:
            return run
        update_run_row(row, run)
        await self._session.flush()
        return to_run_domain(row)

    async def add_transition(self, transition: RunTransitionRecord) -> RunTransitionRecord:
        row = RunTransitionRow(
            id=transition.id,
            run_id=transition.run_id,
            from_status=transition.from_status.value,
            to_status=transition.to_status.value,
            changed_at=transition.changed_at,
            reason=transition.reason,
        )
        self._session.add(row)
        await self._session.flush()
        return to_transition_domain(row)
