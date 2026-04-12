from dataclasses import asdict
from uuid import UUID

from researchlens.modules.retrieval.application.ports import (
    RetrievalIngestionRepository,
    SearchProvider,
)
from researchlens.modules.retrieval.application.retrieval_stage_steps import (
    RetrievalPlanningResult,
    RetrievalSelectionResult,
    RetrievalStageSteps,
)
from researchlens.modules.retrieval.domain.summary import RetrievalSummary
from researchlens.modules.retrieval.orchestration.progress import (
    RetrievalGraphCheckpointSink,
    RetrievalGraphEventSink,
)
from researchlens.shared.config import ResearchLensSettings
from researchlens.shared.embeddings.factory import build_embedding_client
from researchlens.shared.embeddings.ports import EmbeddingClient
from researchlens.shared.llm.factory import build_llm_client
from researchlens.shared.llm.ports import StructuredGenerationClient


class RetrievalGraphRuntime:
    def __init__(
        self,
        *,
        settings: ResearchLensSettings,
        events: RetrievalGraphEventSink,
        checkpoints: RetrievalGraphCheckpointSink,
        primary_provider: SearchProvider,
        fallback_providers: tuple[SearchProvider, ...],
        ingestion_repository: RetrievalIngestionRepository | None = None,
        llm_client: StructuredGenerationClient | None = None,
        embedding_client: EmbeddingClient | None = None,
    ) -> None:
        retrieval_settings = settings.retrieval
        self._events = events
        self._checkpoints = checkpoints
        self._steps = RetrievalStageSteps(
            settings=retrieval_settings,
            primary_provider=primary_provider,
            fallback_providers=fallback_providers,
            ingestion_repository=ingestion_repository,
            llm_client=llm_client or _configured_llm(settings),
            embedding_client=embedding_client or _configured_embedding(settings),
            embedding_settings=settings.embeddings,
        )

    async def plan(self, *, question: str) -> RetrievalPlanningResult:
        await self._events.info(
            key="retrieval:outline-started",
            message="Retrieval outline generation started",
            payload={},
        )
        await self._events.info(
            key="retrieval:query-planning-started",
            message="Retrieval query planning started",
            payload={},
        )
        return await self._steps.plan(question=question)

    async def select_sources(
        self,
        *,
        planning: RetrievalPlanningResult,
        question: str,
    ) -> RetrievalSelectionResult:
        await self._events.info(
            key="retrieval:search-started",
            message="Retrieval provider search started",
            payload={"planned_queries": len(planning.query_plan.queries)},
        )
        return await self._steps.select_sources(
            query_plan=planning.query_plan,
            question=question,
        )

    async def finalize(
        self,
        *,
        run_id: UUID,
        planning: RetrievalPlanningResult,
        selection: RetrievalSelectionResult,
        completed_stages: tuple[str, ...],
    ) -> RetrievalSummary:
        summary = await self._steps.enrich_and_ingest(
            run_id=run_id,
            planning=planning,
            selection=selection,
        )
        await self._emit_summary_events(summary)
        payload = asdict(summary)
        payload["run_id"] = str(summary.run_id)
        await self._checkpoints.checkpoint(
            key="retrieval:summary",
            summary=payload,
            completed_stages=completed_stages,
            next_stage="draft",
        )
        await self._events.info(
            key="retrieval:summary-completed",
            message="Retrieval summary completed",
            payload=payload,
        )
        return summary

    async def _emit_summary_events(self, summary: RetrievalSummary) -> None:
        if summary.fallback_used:
            await self._events.warning(
                key="retrieval:provider-fallback-used",
                message="Direct provider fallback was used",
                payload={"reason": "primary yielded too few normalized candidates"},
            )
        if summary.provider_failures:
            await self._events.warning(
                key="retrieval:provider-failures",
                message="One or more retrieval providers failed",
                payload={"providers": list(summary.provider_failures)},
            )
        if summary.planning_warnings:
            await self._events.warning(
                key="retrieval:planning-fallbacks",
                message="Retrieval planning used fallback behavior",
                payload={"warnings": list(summary.planning_warnings)},
            )


def _configured_llm(settings: ResearchLensSettings) -> StructuredGenerationClient | None:
    if settings.llm.provider == "disabled" or not settings.llm.api_key:
        return None
    return build_llm_client(settings.llm)


def _configured_embedding(settings: ResearchLensSettings) -> EmbeddingClient | None:
    if settings.embeddings.provider == "disabled" or not settings.embeddings.api_key:
        return None
    return build_embedding_client(settings.embeddings)
