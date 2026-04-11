from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.runs.application.ports import RunCheckpointStore
from researchlens.modules.runs.domain import RunCheckpointRecord, RunStage
from researchlens.modules.runs.infrastructure.mappers import to_checkpoint_domain
from researchlens.modules.runs.infrastructure.rows import RunCheckpointRow


class SqlAlchemyRunCheckpointStore(RunCheckpointStore):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        *,
        run_id: UUID,
        stage: RunStage,
        checkpoint_key: str,
        payload_json: dict[str, Any] | None,
        summary_json: dict[str, Any] | None,
        created_at: datetime,
    ) -> RunCheckpointRecord:
        statement = select(RunCheckpointRow).where(
            RunCheckpointRow.run_id == run_id,
            RunCheckpointRow.checkpoint_key == checkpoint_key,
        )
        existing = await self._session.scalar(statement)
        if existing is not None:
            return to_checkpoint_domain(existing)
        row = RunCheckpointRow(
            id=uuid4(),
            run_id=run_id,
            stage=stage.value,
            checkpoint_key=checkpoint_key,
            payload_json=payload_json,
            summary_json=summary_json,
            created_at=created_at,
        )
        self._session.add(row)
        await self._session.flush()
        return to_checkpoint_domain(row)

    async def latest_for_run(self, *, run_id: UUID) -> RunCheckpointRecord | None:
        statement = (
            select(RunCheckpointRow)
            .where(RunCheckpointRow.run_id == run_id)
            .order_by(RunCheckpointRow.created_at.desc(), RunCheckpointRow.id.desc())
        )
        row = await self._session.scalar(statement)
        return to_checkpoint_domain(row) if row is not None else None

    async def list_for_run(self, *, run_id: UUID) -> list[RunCheckpointRecord]:
        statement = (
            select(RunCheckpointRow)
            .where(RunCheckpointRow.run_id == run_id)
            .order_by(RunCheckpointRow.created_at.asc(), RunCheckpointRow.id.asc())
        )
        rows = await self._session.scalars(statement)
        return [to_checkpoint_domain(row) for row in rows]
