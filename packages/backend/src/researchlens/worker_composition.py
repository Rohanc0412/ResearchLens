from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.retrieval.infrastructure.persistence.source_repository_sql import (
    SqlAlchemyRetrievalIngestionRepository,
)
from researchlens.modules.retrieval.orchestration import RetrievalStageOrchestrator
from researchlens.modules.runs.application import ProcessRunQueueItemCommand
from researchlens.modules.runs.application.ports import RunCheckpointStore, RunEventStore
from researchlens.modules.runs.application.stage_execution_controller import (
    SleepStageExecutionController,
)
from researchlens.modules.runs.domain import (
    Run,
    RunEventAudience,
    RunEventLevel,
    RunEventType,
    RunStage,
)
from researchlens.modules.runs.infrastructure import SqlAlchemyRunsRuntime
from researchlens.modules.runs.infrastructure.runtime import RunsRequestContext
from researchlens.shared.config import ResearchLensSettings
from researchlens.shared.db import DatabaseRuntime
from researchlens.shared.db.transaction_manager import SqlAlchemyTransactionManager
from researchlens.shared.embeddings.factory import build_embedding_client


class WorkerRunsRuntime(Protocol):
    def request_context(self) -> AbstractAsyncContextManager[RunsRequestContext]: ...


def build_worker_runs_runtime(
    *,
    database: DatabaseRuntime,
    settings: ResearchLensSettings,
) -> WorkerRunsRuntime:
    return SqlAlchemyRunsRuntime(
        database.session_factory,
        settings,
        stage_controller_factory=lambda **kwargs: RetrievalStageExecutionController(
            settings=settings,
            session=kwargs["session"],
            event_store=kwargs["event_store"],
            checkpoint_store=kwargs["checkpoint_store"],
            transaction_manager=kwargs["transaction_manager"],
            fallback=SleepStageExecutionController(settings.queue.run_stub_stage_delay_ms),
        ),
    )


class RetrievalStageExecutionController:
    def __init__(
        self,
        *,
        settings: ResearchLensSettings,
        session: AsyncSession,
        event_store: RunEventStore,
        checkpoint_store: RunCheckpointStore,
        transaction_manager: SqlAlchemyTransactionManager,
        fallback: SleepStageExecutionController,
    ) -> None:
        self._settings = settings
        self._session = session
        self._event_store = event_store
        self._checkpoint_store = checkpoint_store
        self._transaction_manager = transaction_manager
        self._fallback = fallback

    async def before_stage(self, *, run: Run, stage: RunStage) -> None:
        if stage != RunStage.RETRIEVE:
            await self._fallback.before_stage(run=run, stage=stage)
            return
        ingestion_repository = SqlAlchemyRetrievalIngestionRepository(
            self._session,
            embedding_model=self._settings.embeddings.model,
            embedding_client=(
                build_embedding_client(self._settings.embeddings)
                if self._settings.embeddings.provider != "disabled"
                and self._settings.embeddings.api_key
                else None
            ),
        )
        orchestrator = RetrievalStageOrchestrator(
            settings=self._settings,
            ingestion_repository=ingestion_repository,
        )
        events = _RetrievalRunEventWriter(
            run=run,
            event_store=self._event_store,
            transaction_manager=self._transaction_manager,
        )
        checkpoints = _RetrievalRunCheckpointWriter(
            run=run,
            checkpoint_store=self._checkpoint_store,
            transaction_manager=self._transaction_manager,
        )
        await orchestrator.execute(
            run_id=run.id,
            research_question=await self._research_question_for_run(run),
            events=events,
            checkpoints=checkpoints,
        )

    async def after_stage(self, *, run: Run, stage: RunStage) -> None:
        await self._fallback.after_stage(run=run, stage=stage)

    async def _research_question_for_run(self, run: Run) -> str:
        events = await self._event_store.list_for_run(
            run_id=run.id,
            after_event_number=None,
        )
        for event in events:
            if event.event_type == RunEventType.RUN_CREATED and event.payload_json:
                request_text = event.payload_json.get("request_text")
                if isinstance(request_text, str) and request_text.strip():
                    return request_text
        return f"{run.output_type} run {run.id}"


class _RetrievalRunEventWriter:
    def __init__(
        self,
        *,
        run: Run,
        event_store: RunEventStore,
        transaction_manager: SqlAlchemyTransactionManager,
    ) -> None:
        self._run = run
        self._event_store = event_store
        self._transaction_manager = transaction_manager

    async def info(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        await self._append(key=key, level=RunEventLevel.INFO, message=message, payload=payload)

    async def warning(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        await self._append(key=key, level=RunEventLevel.WARN, message=message, payload=payload)

    async def _append(
        self,
        *,
        key: str,
        level: RunEventLevel,
        message: str,
        payload: dict[str, object],
    ) -> None:
        async with self._transaction_manager.boundary():
            await self._event_store.append(
                run_id=self._run.id,
                event_type=RunEventType.CHECKPOINT_WRITTEN,
                audience=RunEventAudience.PROGRESS,
                level=level,
                status=self._run.status.value,
                stage=RunStage.RETRIEVE.value,
                message=message,
                payload_json=payload,
                retry_count=self._run.retry_count,
                cancel_requested=self._run.cancel_requested_at is not None,
                created_at=datetime.now(tz=UTC),
                event_key=f"attempt-{self._run.retry_count}:{key}",
            )


class _RetrievalRunCheckpointWriter:
    def __init__(
        self,
        *,
        run: Run,
        checkpoint_store: RunCheckpointStore,
        transaction_manager: SqlAlchemyTransactionManager,
    ) -> None:
        self._run = run
        self._checkpoint_store = checkpoint_store
        self._transaction_manager = transaction_manager

    async def checkpoint(self, *, key: str, summary: dict[str, object]) -> None:
        async with self._transaction_manager.boundary():
            await self._checkpoint_store.append(
                run_id=self._run.id,
                stage=RunStage.RETRIEVE,
                checkpoint_key=f"attempt-{self._run.retry_count}:{key}",
                payload_json=summary,
                summary_json=summary,
                created_at=datetime.now(tz=UTC),
            )


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
