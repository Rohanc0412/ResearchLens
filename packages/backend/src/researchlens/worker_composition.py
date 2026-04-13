from contextlib import AbstractAsyncContextManager
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.drafting.infrastructure import (
    SqlAlchemyDraftingRepository,
    SqlAlchemyDraftingRunInputReader,
)
from researchlens.modules.drafting.orchestration import DraftingGraphRuntime
from researchlens.modules.evaluation.application.ports import SectionGroundingEvaluator
from researchlens.modules.evaluation.infrastructure import (
    SqlAlchemyEvaluationInputReader,
    SqlAlchemyEvaluationRepository,
)
from researchlens.modules.evaluation.infrastructure.ragas import (
    RagasAssistedClaimExtractor,
    RagasFaithfulnessScorer,
    RagasGroundingEvaluator,
)
from researchlens.modules.evaluation.orchestration import EvaluationGraphRuntime
from researchlens.modules.repair.infrastructure import SqlAlchemyRepairRepository
from researchlens.modules.repair.orchestration import RepairGraphRuntime
from researchlens.modules.retrieval.infrastructure.persistence.source_repository_sql import (
    SqlAlchemyRetrievalIngestionRepository,
)
from researchlens.modules.retrieval.infrastructure.providers.provider_registry import (
    build_provider_registry,
)
from researchlens.modules.retrieval.orchestration import RetrievalGraphRuntime
from researchlens.modules.runs.application import UtcRunClock
from researchlens.modules.runs.application.ports import RunCheckpointStore, RunEventStore
from researchlens.modules.runs.domain import RunStage
from researchlens.modules.runs.infrastructure import SqlAlchemyRunsRuntime
from researchlens.modules.runs.infrastructure.queue_backend_db import DbRunQueueBackend
from researchlens.modules.runs.infrastructure.run_repository_sql import SqlAlchemyRunRepository
from researchlens.modules.runs.infrastructure.runtime import RunsRequestContext
from researchlens.modules.runs.orchestration import LangGraphRunOrchestrator, RunGraphRuntimeBridge
from researchlens.shared.config import ResearchLensSettings
from researchlens.shared.db import DatabaseRuntime
from researchlens.shared.db.transaction_manager import SqlAlchemyTransactionManager
from researchlens.shared.embeddings.factory import build_embedding_client
from researchlens.shared.llm.factory import build_llm_client
from researchlens.shared.llm.ports import StructuredGenerationClient
from researchlens.worker_polling import poll_worker_once
from researchlens.worker_stage_factories import stage_factories

__all__ = ["build_worker_runs_runtime", "poll_worker_once"]


class WorkerRunsRuntime(Protocol):
    def request_context(self) -> AbstractAsyncContextManager[RunsRequestContext]: ...


def build_worker_runs_runtime(
    *,
    database: DatabaseRuntime,
    settings: ResearchLensSettings,
    drafting_llm_client: StructuredGenerationClient | None = None,
    evaluation_evaluator: SectionGroundingEvaluator | None = None,
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
            evaluation_evaluator=evaluation_evaluator,
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
    evaluation_evaluator: SectionGroundingEvaluator | None,
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
    retrieval_providers = build_provider_registry(settings.retrieval)
    primary_retrieval_provider = retrieval_providers[settings.retrieval.primary_provider]
    fallback_retrieval_providers = tuple(
        provider
        for name, provider in retrieval_providers.items()
        if name in settings.retrieval.fallback_providers
    )
    factories = stage_factories(
        settings=settings,
        session=session,
        bridge=bridge,
        drafting_llm_client=drafting_llm_client,
        evaluation_evaluator=evaluation_evaluator,
        retrieval_providers=(primary_retrieval_provider, fallback_retrieval_providers),
        builders=(
            _build_retrieval_runtime,
            _build_drafting_runtime,
            _build_evaluation_runtime,
            _build_repair_runtime,
        ),
    )
    return LangGraphRunOrchestrator(
        bridge=bridge,
        retrieval_subgraph_factory=factories[0],
        drafting_subgraph_factory=factories[1],
        evaluation_subgraph_factory=factories[2],
        repair_subgraph_factory=factories[3],
        reevaluation_subgraph_factory=factories[4],
    )


def _build_retrieval_runtime(
    *,
    settings: ResearchLensSettings,
    session: AsyncSession,
    bridge: RunGraphRuntimeBridge,
    state: object,
    primary_retrieval_provider: object,
    fallback_retrieval_providers: tuple[object, ...],
) -> RetrievalGraphRuntime:
    return RetrievalGraphRuntime(
        settings=settings,
        events=bridge.stage_event_sink(state=state, stage=RunStage.RETRIEVE),  # type: ignore[arg-type]
        checkpoints=bridge.stage_checkpoint_sink(
            state=state, stage=RunStage.RETRIEVE  # type: ignore[arg-type]
        ),
        primary_provider=primary_retrieval_provider,  # type: ignore[arg-type]
        fallback_providers=fallback_retrieval_providers,  # type: ignore[arg-type]
        ingestion_repository=SqlAlchemyRetrievalIngestionRepository(
            session,
            embedding_model=settings.embeddings.model,
            embedding_client=(
                build_embedding_client(settings.embeddings)
                if settings.embeddings.provider != "disabled" and settings.embeddings.api_key
                else None
            ),
        ),
    )


def _build_drafting_runtime(
    *,
    settings: ResearchLensSettings,
    session: AsyncSession,
    bridge: RunGraphRuntimeBridge,
    state: object,
    drafting_llm_client: StructuredGenerationClient | None,
) -> DraftingGraphRuntime:
    return DraftingGraphRuntime(
        settings=settings,
        input_reader=SqlAlchemyDraftingRunInputReader(session),
        repository=SqlAlchemyDraftingRepository(session),
        cancellation_probe=_RunCancellationProbe(session),
        events=bridge.stage_event_sink(state=state, stage=RunStage.DRAFT),  # type: ignore[arg-type]
        checkpoints=bridge.stage_checkpoint_sink(
            state=state, stage=RunStage.DRAFT  # type: ignore[arg-type]
        ),
        generation_client=drafting_llm_client,
    )


def _build_evaluation_runtime(
    *,
    settings: ResearchLensSettings,
    session: AsyncSession,
    bridge: RunGraphRuntimeBridge,
    state: object,
    evaluation_evaluator: SectionGroundingEvaluator | None,
) -> EvaluationGraphRuntime:
    return EvaluationGraphRuntime(
        settings=settings,
        input_reader=SqlAlchemyEvaluationInputReader(session),
        repository=SqlAlchemyEvaluationRepository(session),
        evaluator=evaluation_evaluator or _build_evaluation_evaluator(settings),
        cancellation_probe=_RunCancellationProbe(session),
        events=bridge.stage_event_sink(state=state, stage=RunStage.EVALUATE),  # type: ignore[arg-type]
        checkpoints=bridge.stage_checkpoint_sink(
            state=state, stage=RunStage.EVALUATE  # type: ignore[arg-type]
        ),
    )


def _build_repair_runtime(
    *,
    settings: ResearchLensSettings,
    session: AsyncSession,
    bridge: RunGraphRuntimeBridge,
    state: object,
    repair_llm_client: StructuredGenerationClient | None,
) -> RepairGraphRuntime:
    return RepairGraphRuntime(
        settings=settings,
        repository=SqlAlchemyRepairRepository(session),
        generation_client=repair_llm_client or build_llm_client(settings.llm),
        cancellation_probe=_RunCancellationProbe(session),
        events=bridge.stage_event_sink(state=state, stage=RunStage.REPAIR),  # type: ignore[arg-type]
        checkpoints=bridge.stage_checkpoint_sink(
            state=state, stage=RunStage.REPAIR  # type: ignore[arg-type]
        ),
    )


def _build_evaluation_evaluator(settings: ResearchLensSettings) -> SectionGroundingEvaluator:
    return RagasGroundingEvaluator(
        claim_extractor=RagasAssistedClaimExtractor(
            settings=settings.evaluation,
            generation_client=build_llm_client(settings.llm),
        ),
        faithfulness_scorer=RagasFaithfulnessScorer(
            provider=settings.llm.provider,
            model=settings.llm.model,
            api_key=settings.llm.api_key,
            base_url=settings.llm.base_url,
            timeout_seconds=settings.llm.timeout_seconds,
        ),
    )


class _RunCancellationProbe:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = SqlAlchemyRunRepository(session)

    async def cancel_requested(self, *, run_id: UUID) -> bool:
        run = await self._repository.get_by_id(run_id=run_id)
        return run is not None and run.cancel_requested_at is not None
