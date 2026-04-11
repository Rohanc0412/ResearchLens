from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime, timedelta
from typing import Protocol

from researchlens.modules.runs.application import ProcessRunQueueItemCommand
from researchlens.modules.runs.infrastructure import SqlAlchemyRunsRuntime
from researchlens.modules.runs.infrastructure.runtime import RunsRequestContext
from researchlens.shared.config import ResearchLensSettings
from researchlens.shared.db import DatabaseRuntime


class WorkerRunsRuntime(Protocol):
    def request_context(self) -> AbstractAsyncContextManager[RunsRequestContext]: ...


def build_worker_runs_runtime(
    *,
    database: DatabaseRuntime,
    settings: ResearchLensSettings,
) -> WorkerRunsRuntime:
    return SqlAlchemyRunsRuntime(database.session_factory, settings)


async def poll_worker_once(
    *,
    runs_runtime: WorkerRunsRuntime,
    settings: ResearchLensSettings,
) -> None:
    async with runs_runtime.request_context() as context:
        async with context.transaction_manager.boundary():
            queue_items = await context.queue_backend.claim_available(
                now=datetime.now(tz=UTC),
                lease_duration=timedelta(seconds=settings.queue.lease_seconds),
                limit=settings.queue.batch_size,
                max_attempts=settings.queue.max_attempts,
            )
        for queue_item in queue_items:
            if queue_item.lease_token is None:
                continue
            await context.process_run_queue_item.execute(
                ProcessRunQueueItemCommand(
                    queue_item_id=queue_item.id,
                    lease_token=queue_item.lease_token,
                    run_id=queue_item.run_id,
                )
            )
