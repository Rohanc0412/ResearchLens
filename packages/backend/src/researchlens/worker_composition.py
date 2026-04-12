from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.drafting.infrastructure import (
    SqlAlchemyDraftingRepository,
    SqlAlchemyDraftingRunInputReader,
)
from researchlens.modules.drafting.orchestration import (
    DraftingGraphRuntime,
    build_drafting_subgraph,
)
from researchlens.modules.retrieval.infrastructure.persistence.source_repository_sql import (
    SqlAlchemyRetrievalIngestionRepository,
)
from researchlens.modules.retrieval.orchestration import (
    RetrievalGraphRuntime,
    build_retrieval_subgraph,
)
from researchlens.modules.runs.application import ProcessRunQueueItemCommand, UtcRunClock
from researchlens.modules.runs.application.ports import RunCheckpointStore, RunEventStore
from researchlens.modules.runs.domain import RunStage
from researchlens.modules.runs.infrastructure import SqlAlchemyRunsRuntime
from researchlens.modules.runs.infrastructure.queue_backend_db import DbRunQueueBackend
from researchlens.modules.runs.infrastructure.run_repository_sql import SqlAlchemyRunRepository
from researchlens.modules.runs.infrastructure.runtime import RunsRequestContext
from researchlens.modules.runs.orchestration import (
    LangGraphRunOrchestrator,
    RunGraphRuntimeBridge,
)
from researchlens.shared.config import ResearchLensSettings
from researchlens.shared.db import DatabaseRuntime
from researchlens.shared.db.transaction_manager import SqlAlchemyTransactionManager
from researchlens.shared.embeddings.factory import build_embedding_client
from researchlens.shared.llm.ports import StructuredGenerationClient


class WorkerRunsRuntime(Protocol):
    def request_context(self) -> AbstractAsyncContextManager[RunsRequestContext]: ...


def build_worker_runs_runtime(
    *,
    database: DatabaseRuntime,
    settings: ResearchLensSettings,
    drafting_llm_client: StructuredGenerationClient | None = None,
) -> WorkerRunsRuntime:
    return SqlAlchemyRunsRuntime(
        database.session_factory,
        settings,
        run_orchestrator_factory=lambda **kwargs: _build_run_orchestrator(
            settings=settings,
            session=kwargs["session"],
            event_store=kwargs["event_store"],
            checkpoint_store=kwargs["checkpoint_store"],
            transaction_manager=kwargs["transaction_manager"],
            drafting_llm_client=drafting_llm_client,
        ),
    )


def _build_run_orchestrator(
    *,
    settings: ResearchLensSettings,
    session: AsyncSession,
    event_store: RunEventStore,
    checkpoint_store: RunCheckpointStore,
    transaction_manager: SqlAlchemyTransactionManager,
    drafting_llm_client: StructuredGenerationClient | None,
) -> LangGraphRunOrchestrator:
    bridge = RunGraphRuntimeBridge(
        run_repository=SqlAlchemyRunRepository(session),
        event_store=event_store,
        checkpoint_store=checkpoint_store,
        queue_backend=DbRunQueueBackend(session),
        transaction_manager=transaction_manager,
        clock=UtcRunClock(),
        queue_lease_seconds=settings.queue.lease_seconds,
    )
    return LangGraphRunOrchestrator(
        bridge=bridge,
        retrieval_subgraph_factory=lambda state: build_retrieval_subgraph(
            RetrievalGraphRuntime(
                settings=settings,
                events=bridge.stage_event_sink(state=state, stage=RunStage.RETRIEVE),
                checkpoints=bridge.stage_checkpoint_sink(state=state, stage=RunStage.RETRIEVE),
                ingestion_repository=SqlAlchemyRetrievalIngestionRepository(
                    session,
                    embedding_model=settings.embeddings.model,
                    embedding_client=(
                        build_embedding_client(settings.embeddings)
                        if settings.embeddings.provider != "disabled"
                        and settings.embeddings.api_key
                        else None
                    ),
                ),
            )
        ),
        drafting_subgraph_factory=lambda state: build_drafting_subgraph(
            DraftingGraphRuntime(
                settings=settings,
                input_reader=SqlAlchemyDraftingRunInputReader(session),
                repository=SqlAlchemyDraftingRepository(session),
                cancellation_probe=_RunCancellationProbe(session),
                events=bridge.stage_event_sink(state=state, stage=RunStage.DRAFT),
                checkpoints=bridge.stage_checkpoint_sink(state=state, stage=RunStage.DRAFT),
                generation_client=drafting_llm_client,
            )
        ),
    )


class _RunCancellationProbe:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = SqlAlchemyRunRepository(session)

    async def cancel_requested(self, *, run_id: UUID) -> bool:
        run = await self._repository.get_by_id(run_id=run_id)
        return run is not None and run.cancel_requested_at is not None


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
