from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.drafting.infrastructure import (
    SqlAlchemyDraftingRepository,
    SqlAlchemyDraftingRunInputReader,
)
from researchlens.modules.drafting.orchestration import DraftingStageOrchestrator
from researchlens.modules.retrieval.infrastructure.persistence.source_repository_sql import (
    SqlAlchemyRetrievalIngestionRepository,
)
from researchlens.modules.retrieval.orchestration import RetrievalStageOrchestrator
from researchlens.modules.runs.application import ProcessRunQueueItemCommand
from researchlens.modules.runs.application.ports import RunCheckpointStore, RunEventStore
from researchlens.modules.runs.application.stage_execution_controller import (
    SleepStageExecutionController,
)
from researchlens.modules.runs.application.stage_progress_writers import (
    StageRunCheckpointWriter,
    StageRunEventWriter,
)
from researchlens.modules.runs.domain import (
    Run,
    RunEventType,
    RunStage,
)
from researchlens.modules.runs.infrastructure import SqlAlchemyRunsRuntime
from researchlens.modules.runs.infrastructure.run_repository_sql import SqlAlchemyRunRepository
from researchlens.modules.runs.infrastructure.runtime import RunsRequestContext
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
        stage_controller_factory=lambda **kwargs: ResearchStageExecutionController(
            settings=settings,
            session=kwargs["session"],
            event_store=kwargs["event_store"],
            checkpoint_store=kwargs["checkpoint_store"],
            transaction_manager=kwargs["transaction_manager"],
            drafting_llm_client=drafting_llm_client,
            fallback=SleepStageExecutionController(settings.queue.run_stub_stage_delay_ms),
        ),
    )


class ResearchStageExecutionController:
    def __init__(
        self,
        *,
        settings: ResearchLensSettings,
        session: AsyncSession,
        event_store: RunEventStore,
        checkpoint_store: RunCheckpointStore,
        transaction_manager: SqlAlchemyTransactionManager,
        drafting_llm_client: StructuredGenerationClient | None,
        fallback: SleepStageExecutionController,
    ) -> None:
        self._settings = settings
        self._session = session
        self._event_store = event_store
        self._checkpoint_store = checkpoint_store
        self._transaction_manager = transaction_manager
        self._drafting_llm_client = drafting_llm_client
        self._fallback = fallback

    async def before_stage(self, *, run: Run, stage: RunStage) -> None:
        if stage == RunStage.RETRIEVE:
            await self._run_retrieval_stage(run)
            return
        if stage == RunStage.DRAFT:
            await self._run_drafting_stage(run)
            return
        await self._fallback.before_stage(run=run, stage=stage)

    async def _run_retrieval_stage(self, run: Run) -> None:
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
        events = StageRunEventWriter(
            stage=RunStage.RETRIEVE,
            run=run,
            event_store=self._event_store,
            transaction_manager=self._transaction_manager,
        )
        checkpoints = StageRunCheckpointWriter(
            stage=RunStage.RETRIEVE,
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

    async def _run_drafting_stage(self, run: Run) -> None:
        if not self._settings.drafting.enabled:
            raise ValueError("Drafting is disabled by configuration.")
        input_reader = SqlAlchemyDraftingRunInputReader(self._session)
        repository = SqlAlchemyDraftingRepository(self._session)
        orchestrator = DraftingStageOrchestrator(
            settings=self._settings,
            input_reader=input_reader,
            repository=repository,
            cancellation_probe=_RunCancellationProbe(self._session),
            generation_client=self._drafting_llm_client,
        )
        events = StageRunEventWriter(
            stage=RunStage.DRAFT,
            run=run,
            event_store=self._event_store,
            transaction_manager=self._transaction_manager,
        )
        checkpoints = StageRunCheckpointWriter(
            stage=RunStage.DRAFT,
            run=run,
            checkpoint_store=self._checkpoint_store,
            transaction_manager=self._transaction_manager,
        )
        await orchestrator.execute(
            run_id=run.id,
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
