import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import asdict
from typing import Protocol
from uuid import UUID

from researchlens.modules.runs.application import GetRunQuery, ListRunEventsQuery
from researchlens.modules.runs.application.dto import RunEventView, RunSummaryView


class ListRunEventsReader(Protocol):
    async def execute(self, query: ListRunEventsQuery) -> list[RunEventView]: ...


class GetRunReader(Protocol):
    async def execute(self, query: GetRunQuery) -> RunSummaryView: ...


async def stream_run_events(
    *,
    tenant_id: UUID,
    run_id: UUID,
    last_event_id: int | None,
    list_run_events: ListRunEventsReader,
    get_run: GetRunReader,
    keepalive_seconds: int,
    terminal_grace_seconds: int,
) -> AsyncIterator[str]:
    after_event_number = last_event_id
    terminal_seen_at = None
    loop = asyncio.get_running_loop()
    while True:
        events = await list_run_events.execute(
            ListRunEventsQuery(
                tenant_id=tenant_id,
                run_id=run_id,
                after_event_number=after_event_number,
            )
        )
        for event in events:
            after_event_number = event.event_number
            yield f"event: {event.event_type}\n"
            yield f"id: {event.event_number}\n"
            yield f"data: {json.dumps(asdict(event), default=str)}\n\n"

        run = await get_run.execute(GetRunQuery(tenant_id=tenant_id, run_id=run_id))
        if run.status in {"succeeded", "failed", "canceled"}:
            if terminal_seen_at is None:
                terminal_seen_at = loop.time()
            elif loop.time() - terminal_seen_at >= terminal_grace_seconds:
                break
        else:
            terminal_seen_at = None

        yield ": keepalive\n\n"
        await asyncio.sleep(keepalive_seconds)
