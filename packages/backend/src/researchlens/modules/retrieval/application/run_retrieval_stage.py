from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.retrieval.application.enrich_selected_candidates import (
    EnrichmentRouter,
    enrich_candidates,
)
from researchlens.modules.retrieval.application.generate_retrieval_outline import (
    GenerateRetrievalOutlineUseCase,
    deterministic_retrieval_outline,
)
from researchlens.modules.retrieval.application.plan_queries_from_outline import (
    DeterministicQueryPlanner,
    _query_plan_from_data,
    build_query_plan_request,
)
from researchlens.modules.retrieval.application.ports import (
    RetrievalIngestionRepository,
    SearchProvider,
)
from researchlens.modules.retrieval.application.rerank_with_embeddings import EmbeddingReranker
from researchlens.modules.retrieval.application.search_candidates import (
    SearchCandidatesResult,
    SearchCandidatesUseCase,
)
from researchlens.modules.retrieval.domain.candidate import NormalizedSearchCandidate
from researchlens.modules.retrieval.domain.diversification_policy import diversify_candidates
from researchlens.modules.retrieval.domain.query_plan import QueryPlan
from researchlens.modules.retrieval.domain.ranking_policy import (
    RankedCandidate,
    RankingWeights,
    rank_candidates,
)
from researchlens.modules.retrieval.domain.retrieval_outline import RetrievalOutline
from researchlens.modules.retrieval.domain.summary import RetrievalSummary
from researchlens.shared.config.embeddings import EmbeddingsSettings
from researchlens.shared.config.retrieval import RetrievalSettings
from researchlens.shared.embeddings.ports import EmbeddingClient
from researchlens.shared.llm.ports import StructuredGenerationClient


@dataclass(frozen=True, slots=True)
class RunRetrievalStageCommand:
    run_id: UUID
    research_question: str


class RunRetrievalStageUseCase:
    def __init__(
        self,
        *,
        settings: RetrievalSettings,
        primary_provider: SearchProvider,
        fallback_providers: tuple[SearchProvider, ...],
        ingestion_repository: RetrievalIngestionRepository | None = None,
        llm_client: StructuredGenerationClient | None = None,
        embedding_client: EmbeddingClient | None = None,
        embedding_settings: EmbeddingsSettings | None = None,
    ) -> None:
        self._settings = settings
        self._primary_provider = primary_provider
        self._fallback_providers = fallback_providers
        self._ingestion_repository = ingestion_repository
        self._llm_client = llm_client
        self._embedding_client = embedding_client
        self._embedding_settings = embedding_settings
        self._planning_warnings: list[str] = []

    async def execute(self, command: RunRetrievalStageCommand) -> RetrievalSummary:
        self._planning_warnings = []
        outline = await self._generate_outline(command.research_question)
        query_plan = await self._plan_queries(command.research_question, outline)
        search_result = await self._search_candidates(query_plan)
        ranked = await self._rank_candidates(search_result, query_plan, command.research_question)
        selected = diversify_candidates(
            ranked,
            max_selected=self._settings.max_selected_sources,
            per_bucket_limit=self._settings.diversity_per_bucket_limit,
        )
        enriched_selected = await self._enrich_selected(selected)
        ingested_sources = await self._ingest_selected(command, enriched_selected)
        return self._summary(
            command=command,
            outline=outline,
            query_plan=query_plan,
            search_result=search_result,
            selected_count=len(enriched_selected),
            ingested_sources=ingested_sources,
        )

    async def _search_candidates(self, query_plan: QueryPlan) -> SearchCandidatesResult:
        return await SearchCandidatesUseCase(
            primary_provider=self._primary_provider,
            fallback_providers=self._fallback_providers,
            fallback_threshold=self._settings.fallback_threshold,
            max_results_per_provider_query=self._settings.max_results_per_provider_query,
            max_candidates_after_normalization=self._settings.max_candidates_after_normalization,
            max_concurrent_provider_searches=self._settings.max_concurrent_provider_searches,
        ).execute(query_plan)

    async def _rank_candidates(
        self,
        search_result: SearchCandidatesResult,
        query_plan: QueryPlan,
        question: str,
    ) -> list[RankedCandidate]:
        initial_ranked = self._rank_with_embedding_weight(
            candidates=search_result.candidates,
            query_plan=query_plan,
            embedding_weight=0.0,
            embedding_scores={},
        )
        embedding_scores = await self._embedding_scores(initial_ranked, question)
        return self._rank_with_embedding_weight(
            candidates=search_result.candidates,
            query_plan=query_plan,
            embedding_weight=self._settings.ranking_embedding_weight,
            embedding_scores=embedding_scores,
        )

    def _rank_with_embedding_weight(
        self,
        *,
        candidates: list[NormalizedSearchCandidate],
        query_plan: QueryPlan,
        embedding_weight: float,
        embedding_scores: dict[str, float],
    ) -> list[RankedCandidate]:
        return rank_candidates(
            candidates=candidates,
            queries=list(query_plan.queries),
            weights=RankingWeights(
                lexical=self._settings.ranking_lexical_weight,
                embedding=embedding_weight,
                recency=self._settings.ranking_recency_weight,
                citation=self._settings.ranking_citation_weight,
            ),
            embedding_scores=embedding_scores,
        )

    async def _enrich_selected(
        self,
        selected: list[RankedCandidate],
    ) -> list[RankedCandidate]:
        enriched_candidates = await enrich_candidates(
            [item.candidate for item in selected],
            router=EnrichmentRouter(providers=self._provider_map()),
            max_concurrent_fetches=self._settings.max_concurrent_enrichment_fetches,
        )
        return [
            item.__class__(candidate=candidate, score_breakdown=item.score_breakdown)
            for item, candidate in zip(selected, enriched_candidates, strict=False)
        ]

    def _provider_map(self) -> dict[str, SearchProvider]:
        return {
            provider.provider_name: provider
            for provider in (self._primary_provider, *self._fallback_providers)
        }

    async def _ingest_selected(
        self,
        command: RunRetrievalStageCommand,
        selected: list[RankedCandidate],
    ) -> int:
        if self._ingestion_repository is None:
            return 0
        return await self._ingestion_repository.persist_selected_sources(
            run_id=command.run_id,
            selected=selected,
        )

    def _summary(
        self,
        *,
        command: RunRetrievalStageCommand,
        outline: RetrievalOutline,
        query_plan: QueryPlan,
        search_result: SearchCandidatesResult,
        selected_count: int,
        ingested_sources: int,
    ) -> RetrievalSummary:
        return RetrievalSummary(
            run_id=command.run_id,
            outline_sections=len(outline.sections),
            planned_queries=len(query_plan.queries),
            normalized_candidates=len(search_result.candidates),
            selected_sources=selected_count,
            ingested_sources=ingested_sources,
            fallback_used=search_result.fallback_used,
            provider_failures=tuple(
                failure.provider_name for failure in search_result.provider_failures
            ),
            planning_warnings=tuple(self._planning_warnings),
        )

    async def _generate_outline(self, question: str) -> RetrievalOutline:
        if self._llm_client is not None:
            try:
                return await GenerateRetrievalOutlineUseCase(
                    self._llm_client,
                    max_sections=self._settings.max_outline_sections,
                ).execute(question)
            except Exception as exc:
                self._planning_warnings.append(
                    f"outline_generation_failed:{type(exc).__name__}"
                )
        return deterministic_retrieval_outline(question)

    async def _plan_queries(self, question: str, outline: RetrievalOutline) -> QueryPlan:
        if self._llm_client is not None:
            try:
                result = await self._llm_client.generate_structured(
                    build_query_plan_request(question=question, outline=outline)
                )
                plan = _query_plan_from_data(result.data)
                if plan.queries:
                    return plan
            except Exception as exc:
                self._planning_warnings.append(f"query_planning_failed:{type(exc).__name__}")
        return DeterministicQueryPlanner(
            max_global_queries=self._settings.max_global_queries,
            max_queries_per_section=self._settings.max_queries_per_section,
        ).plan(question=question, outline=outline)

    async def _embedding_scores(
        self,
        ranked: list[RankedCandidate],
        question: str,
    ) -> dict[str, float]:
        if self._embedding_client is None:
            return {}
        batch_size = self._embedding_settings.batch_size if self._embedding_settings else 64
        max_concurrent = (
            self._embedding_settings.max_concurrent_batches if self._embedding_settings else 4
        )
        return await EmbeddingReranker(
            client=self._embedding_client,
            batch_size=batch_size,
            max_concurrent_batches=max_concurrent,
        ).score_top_k(
            ranked,
            top_k=self._settings.max_candidates_sent_to_rerank,
            query_text=question,
        )
