import asyncio
from dataclasses import dataclass

from researchlens.modules.retrieval.application.ports import (
    ProviderFailure,
    ProviderSearchRequest,
    SearchProvider,
)
from researchlens.modules.retrieval.domain.candidate import NormalizedSearchCandidate
from researchlens.modules.retrieval.domain.deduplication import deduplicate_candidates
from researchlens.modules.retrieval.domain.query_plan import QueryPlan, RetrievalQuery


@dataclass(frozen=True, slots=True)
class SearchCandidatesResult:
    candidates: list[NormalizedSearchCandidate]
    provider_failures: list[ProviderFailure]
    fallback_used: bool


class SearchCandidatesUseCase:
    def __init__(
        self,
        *,
        primary_provider: SearchProvider,
        fallback_providers: tuple[SearchProvider, ...],
        fallback_threshold: int,
        max_results_per_provider_query: int,
        max_candidates_after_normalization: int,
        max_concurrent_provider_searches: int,
    ) -> None:
        self._primary_provider = primary_provider
        self._fallback_providers = fallback_providers
        self._fallback_threshold = fallback_threshold
        self._max_results = max_results_per_provider_query
        self._max_candidates = max_candidates_after_normalization
        self._search_limiter = asyncio.Semaphore(max_concurrent_provider_searches)

    async def execute(self, query_plan: QueryPlan) -> SearchCandidatesResult:
        failures: list[ProviderFailure] = []
        primary_candidates = await self._search_provider(
            self._primary_provider,
            query_plan,
            failures,
        )
        deduped_primary = deduplicate_candidates(primary_candidates)
        fallback_used = len(deduped_primary) < self._fallback_threshold
        all_candidates = list(deduped_primary)
        if fallback_used:
            fallback_results = await asyncio.gather(
                *[
                    self._search_provider(provider, query_plan, failures)
                    for provider in self._fallback_providers
                ]
            )
            for candidates in fallback_results:
                all_candidates.extend(candidates)
        return SearchCandidatesResult(
            candidates=deduplicate_candidates(all_candidates)[: self._max_candidates],
            provider_failures=failures,
            fallback_used=fallback_used,
        )

    async def _search_provider(
        self,
        provider: SearchProvider,
        query_plan: QueryPlan,
        failures: list[ProviderFailure],
    ) -> list[NormalizedSearchCandidate]:
        try:
            return [
                candidate
                for results in await asyncio.gather(
                    *[self._search_query(provider, query) for query in query_plan.queries]
                )
                for candidate in results
            ]
        except Exception as exc:
            failures.append(
                ProviderFailure(provider.provider_name, "search", f"{type(exc).__name__}: {exc}")
            )
            return []

    async def _search_query(
        self,
        provider: SearchProvider,
        query: RetrievalQuery,
    ) -> list[NormalizedSearchCandidate]:
        async with self._search_limiter:
            return await provider.search(
                ProviderSearchRequest(query=query, max_results=self._max_results)
            )
