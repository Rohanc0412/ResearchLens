from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.runs.application.ports import RunEventStore
from researchlens.modules.runs.domain import (
    RunEventAudience,
    RunEventLevel,
    RunEventRecord,
    RunEventType,
)
from researchlens.modules.runs.infrastructure.mappers import to_event_domain
from researchlens.modules.runs.infrastructure.rows import RunEventRow, RunRow


class SqlAlchemyRunEventStore(RunEventStore):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        *,
        run_id: UUID,
        event_type: RunEventType,
        audience: RunEventAudience,
        level: RunEventLevel,
        status: str,
        stage: str | None,
        message: str,
        payload_json: dict[str, Any] | None,
        retry_count: int,
        cancel_requested: bool,
        created_at: datetime,
        event_key: str | None,
    ) -> RunEventRecord:
        if event_key is not None:
            existing_statement = select(RunEventRow).where(
                RunEventRow.run_id == run_id,
                RunEventRow.event_key == event_key,
            )
            existing = await self._session.scalar(existing_statement)
            if existing is not None:
                return to_event_domain(existing)

        run_row = await self._session.get(RunRow, run_id)
        if run_row is None:
            raise ValueError("Run row was not found for event append.")
        run_row.last_event_number += 1
        row = RunEventRow(
            id=uuid4(),
            run_id=run_id,
            event_number=run_row.last_event_number,
            event_type=event_type.value,
            audience=audience.value,
            level=level.value,
            status=status,
            stage=stage,
            message=message,
            payload_json=payload_json,
            retry_count=retry_count,
            cancel_requested=cancel_requested,
            created_at=created_at,
            event_key=event_key,
        )
        self._session.add(row)
        await self._session.flush()
        return to_event_domain(row)

    async def list_for_run(
        self,
        *,
        run_id: UUID,
        after_event_number: int | None,
    ) -> list[RunEventRecord]:
        statement = select(RunEventRow).where(RunEventRow.run_id == run_id)
        if after_event_number is not None:
            statement = statement.where(RunEventRow.event_number > after_event_number)
        statement = statement.order_by(RunEventRow.event_number.asc())
        rows = await self._session.scalars(statement)
        return [to_event_domain(row) for row in rows]
