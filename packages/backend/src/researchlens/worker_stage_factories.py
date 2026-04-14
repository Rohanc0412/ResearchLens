from collections.abc import Callable
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from researchlens.modules.artifacts.orchestration import (
    ArtifactExportGraphRuntime,
    build_artifact_export_subgraph,
)
from researchlens.modules.drafting.orchestration import (
    DraftingGraphRuntime,
    build_drafting_subgraph,
)
from researchlens.modules.evaluation.application.ports import SectionGroundingEvaluator
from researchlens.modules.evaluation.orchestration import (
    EvaluationGraphRuntime,
    build_evaluation_subgraph,
)
from researchlens.modules.repair.infrastructure import SqlAlchemyRepairRepository
from researchlens.modules.repair.orchestration import RepairGraphRuntime, build_repair_subgraph
from researchlens.modules.retrieval.orchestration import (
    RetrievalGraphRuntime,
    build_retrieval_subgraph,
)
from researchlens.modules.runs.orchestration import RunGraphRuntimeBridge
from researchlens.modules.runs.orchestration.graph import StageSubgraphFactory
from researchlens.repair_reevaluation_subgraph import RepairReevaluationSubgraph
from researchlens.shared.config import ResearchLensSettings
from researchlens.shared.llm.ports import StructuredGenerationClient

RuntimeBuilder = Callable[..., object]


def stage_factories(
    *,
    settings: ResearchLensSettings,
    session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    bridge: RunGraphRuntimeBridge,
    drafting_llm_client: StructuredGenerationClient | None,
    evaluation_evaluator: SectionGroundingEvaluator | None,
    retrieval_providers: tuple[object, tuple[object, ...]],
    builders: tuple[RuntimeBuilder, RuntimeBuilder, RuntimeBuilder, RuntimeBuilder],
    artifact_export_builder: RuntimeBuilder,
) -> tuple[
    StageSubgraphFactory,
    StageSubgraphFactory,
    StageSubgraphFactory,
    StageSubgraphFactory,
    StageSubgraphFactory,
    StageSubgraphFactory,
]:
    return (
        _retrieval(settings, session, bridge, retrieval_providers, builders[0]),
        _drafting(settings, session, session_factory, bridge, drafting_llm_client, builders[1]),
        _evaluation(settings, session, session_factory, bridge, evaluation_evaluator, builders[2]),
        _repair(settings, session, session_factory, bridge, drafting_llm_client, builders[3]),
        _reevaluation(
            settings,
            session,
            session_factory,
            bridge,
            evaluation_evaluator,
            builders[2],
        ),
        _artifact_export(settings, session, bridge, artifact_export_builder),
    )


def _retrieval(
    settings: ResearchLensSettings,
    session: AsyncSession,
    bridge: RunGraphRuntimeBridge,
    providers: tuple[object, tuple[object, ...]],
    builder: RuntimeBuilder,
) -> StageSubgraphFactory:
    return lambda state: build_retrieval_subgraph(
        cast(
            RetrievalGraphRuntime,
            builder(
                settings=settings,
                session=session,
                bridge=bridge,
                state=state,
                primary_retrieval_provider=providers[0],
                fallback_retrieval_providers=providers[1],
            ),
        )
    )


def _drafting(
    settings: ResearchLensSettings,
    session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    bridge: RunGraphRuntimeBridge,
    llm_client: StructuredGenerationClient | None,
    builder: RuntimeBuilder,
) -> StageSubgraphFactory:
    return lambda state: build_drafting_subgraph(
        cast(
            DraftingGraphRuntime,
            builder(
                settings=settings,
                session=session,
                session_factory=session_factory,
                bridge=bridge,
                state=state,
                drafting_llm_client=llm_client,
            ),
        )
    )


def _evaluation(
    settings: ResearchLensSettings,
    session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    bridge: RunGraphRuntimeBridge,
    evaluator: SectionGroundingEvaluator | None,
    builder: RuntimeBuilder,
) -> StageSubgraphFactory:
    return lambda state: build_evaluation_subgraph(
        cast(
            EvaluationGraphRuntime,
            builder(
                settings=settings,
                session=session,
                session_factory=session_factory,
                bridge=bridge,
                state=state,
                evaluation_evaluator=evaluator,
            ),
        )
    )


def _repair(
    settings: ResearchLensSettings,
    session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    bridge: RunGraphRuntimeBridge,
    llm_client: StructuredGenerationClient | None,
    builder: RuntimeBuilder,
) -> StageSubgraphFactory:
    return lambda state: build_repair_subgraph(
        cast(
            RepairGraphRuntime,
            builder(
                settings=settings,
                session=session,
                session_factory=session_factory,
                bridge=bridge,
                state=state,
                repair_llm_client=llm_client,
            ),
        )
    )


def _reevaluation(
    settings: ResearchLensSettings,
    session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    bridge: RunGraphRuntimeBridge,
    evaluator: SectionGroundingEvaluator | None,
    builder: RuntimeBuilder,
) -> StageSubgraphFactory:
    return lambda state: RepairReevaluationSubgraph(
        evaluation_graph=build_evaluation_subgraph(
            cast(
                EvaluationGraphRuntime,
                builder(
                    settings=settings,
                    session=session,
                    session_factory=session_factory,
                    bridge=bridge,
                    state=state,
                    evaluation_evaluator=evaluator,
                ),
            )
        ),
        repair_repository=SqlAlchemyRepairRepository(session),
    )


def _artifact_export(
    settings: ResearchLensSettings,
    session: AsyncSession,
    bridge: RunGraphRuntimeBridge,
    builder: RuntimeBuilder,
) -> StageSubgraphFactory:
    return lambda state: build_artifact_export_subgraph(
        cast(
            ArtifactExportGraphRuntime,
            builder(
                settings=settings,
                session=session,
                bridge=bridge,
                state=state,
            ),
        )
    )
