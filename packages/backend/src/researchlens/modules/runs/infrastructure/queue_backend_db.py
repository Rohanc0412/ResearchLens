from datetime import datetime, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from researchlens.modules.runs.application.ports import RunQueueBackend
from researchlens.modules.runs.domain import RunQueueItem
from researchlens.modules.runs.infrastructure.mappers import to_queue_item_domain
from researchlens.modules.runs.infrastructure.rows import RunQueueItemRow

ACTIVE_QUEUE_STATUSES = ("queued", "leased")


class DbRunQueueBackend(RunQueueBackend):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def enqueue(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
        available_at: datetime,
    ) -> RunQueueItem:
        existing_statement = select(RunQueueItemRow).where(
            RunQueueItemRow.run_id == run_id,
            RunQueueItemRow.status.in_(ACTIVE_QUEUE_STATUSES),
        )
        existing = await self._session.scalar(existing_statement)
        if existing is not None:
            return to_queue_item_domain(existing)
        row = RunQueueItemRow(
            id=uuid4(),
            tenant_id=tenant_id,
            run_id=run_id,
            job_type="run",
            status="queued",
            available_at=available_at,
            lease_token=None,
            leased_at=None,
            lease_expires_at=None,
            attempts=0,
            last_error=None,
            created_at=available_at,
            updated_at=available_at,
        )
        self._session.add(row)
        await self._session.flush()
        return to_queue_item_domain(row)

    async def claim_available(
        self,
        *,
        now: datetime,
        lease_duration: timedelta,
        limit: int,
        max_attempts: int,
    ) -> list[RunQueueItem]:
        if self._session.bind is not None and self._session.bind.dialect.name == "postgresql":
            return await self._claim_postgresql(
                now=now,
                lease_duration=lease_duration,
                limit=limit,
                max_attempts=max_attempts,
            )
        return await self._claim_generic(
            now=now,
            lease_duration=lease_duration,
            limit=limit,
            max_attempts=max_attempts,
        )

    async def heartbeat(
        self,
        *,
        queue_item_id: UUID,
        lease_token: UUID,
        lease_expires_at: datetime,
    ) -> bool:
        statement = (
            update(RunQueueItemRow)
            .where(
                RunQueueItemRow.id == queue_item_id,
                RunQueueItemRow.lease_token == lease_token,
                RunQueueItemRow.status == "leased",
            )
            .values(lease_expires_at=lease_expires_at, updated_at=lease_expires_at)
        )
        result = cast(CursorResult[Any], await self._session.execute(statement))
        return (result.rowcount or 0) > 0

    async def complete(
        self,
        *,
        queue_item_id: UUID,
        lease_token: UUID,
        completed_at: datetime,
    ) -> bool:
        statement = (
            update(RunQueueItemRow)
            .where(
                RunQueueItemRow.id == queue_item_id,
                RunQueueItemRow.lease_token == lease_token,
                RunQueueItemRow.status == "leased",
            )
            .values(
                status="completed",
                lease_token=None,
                leased_at=None,
                lease_expires_at=None,
                updated_at=completed_at,
            )
        )
        result = cast(CursorResult[Any], await self._session.execute(statement))
        return (result.rowcount or 0) > 0

    async def release(
        self,
        *,
        queue_item_id: UUID,
        lease_token: UUID,
        available_at: datetime,
        last_error: str | None,
    ) -> bool:
        statement = (
            update(RunQueueItemRow)
            .where(
                RunQueueItemRow.id == queue_item_id,
                RunQueueItemRow.lease_token == lease_token,
                RunQueueItemRow.status == "leased",
            )
            .values(
                status="queued",
                available_at=available_at,
                lease_token=None,
                leased_at=None,
                lease_expires_at=None,
                last_error=last_error,
                updated_at=available_at,
            )
        )
        result = cast(CursorResult[Any], await self._session.execute(statement))
        return (result.rowcount or 0) > 0

    async def cancel_active_for_run(self, *, run_id: UUID, canceled_at: datetime) -> None:
        statement = (
            update(RunQueueItemRow)
            .where(
                RunQueueItemRow.run_id == run_id,
                RunQueueItemRow.status.in_(ACTIVE_QUEUE_STATUSES),
            )
            .values(
                status="canceled",
                lease_token=None,
                leased_at=None,
                lease_expires_at=None,
                updated_at=canceled_at,
            )
        )
        await self._session.execute(statement)

    async def _claim_postgresql(
        self,
        *,
        now: datetime,
        lease_duration: timedelta,
        limit: int,
        max_attempts: int,
    ) -> list[RunQueueItem]:
        statement = (
            select(RunQueueItemRow)
            .where(_claimable_condition(now, max_attempts=max_attempts))
            .order_by(RunQueueItemRow.available_at.asc(), RunQueueItemRow.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        rows = list(await self._session.scalars(statement))
        claimed: list[RunQueueItem] = []
        for row in rows:
            _lease_queue_item(row=row, now=now, lease_duration=lease_duration)
            claimed.append(to_queue_item_domain(row))
        await self._session.flush()
        return claimed

    async def _claim_generic(
        self,
        *,
        now: datetime,
        lease_duration: timedelta,
        limit: int,
        max_attempts: int,
    ) -> list[RunQueueItem]:
        statement = (
            select(RunQueueItemRow.id)
            .where(_claimable_condition(now, max_attempts=max_attempts))
            .order_by(RunQueueItemRow.available_at.asc(), RunQueueItemRow.created_at.asc())
            .limit(max(limit * 4, limit))
        )
        candidate_ids = list(await self._session.scalars(statement))
        claimed: list[RunQueueItem] = []
        for candidate_id in candidate_ids:
            lease_token = uuid4()
            lease_expires_at = now + lease_duration
            update_statement = (
                update(RunQueueItemRow)
                .where(
                    RunQueueItemRow.id == candidate_id,
                    _claimable_condition(now, max_attempts=max_attempts),
                )
                .values(
                    status="leased",
                    lease_token=lease_token,
                    leased_at=now,
                    lease_expires_at=lease_expires_at,
                    attempts=RunQueueItemRow.attempts + 1,
                    updated_at=now,
                )
            )
            result = cast(CursorResult[Any], await self._session.execute(update_statement))
            if (result.rowcount or 0) == 0:
                continue
            row = await self._session.get(RunQueueItemRow, candidate_id)
            if row is not None:
                claimed.append(to_queue_item_domain(row))
            if len(claimed) >= limit:
                break
        return claimed


def _claimable_condition(
    now: datetime,
    *,
    max_attempts: int,
) -> ColumnElement[bool]:
    return or_(
        and_(
            RunQueueItemRow.status == "queued",
            RunQueueItemRow.available_at <= now,
            RunQueueItemRow.attempts < max_attempts,
        ),
        and_(
            RunQueueItemRow.status == "leased",
            RunQueueItemRow.lease_expires_at.is_not(None),
            RunQueueItemRow.lease_expires_at <= now,
            RunQueueItemRow.attempts < max_attempts,
        ),
    )


def _lease_queue_item(
    *,
    row: RunQueueItemRow,
    now: datetime,
    lease_duration: timedelta,
) -> None:
    row.status = "leased"
    row.lease_token = uuid4()
    row.leased_at = now
    row.lease_expires_at = now + lease_duration
    row.attempts += 1
    row.updated_at = now
