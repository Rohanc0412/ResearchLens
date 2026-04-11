import pytest

from researchlens.modules.retrieval.application.search_candidates import SearchCandidatesUseCase
from researchlens.modules.retrieval.domain.query_plan import QueryIntent, QueryPlan, RetrievalQuery
from researchlens.modules.retrieval.infrastructure.providers.fake_provider import FakeSearchProvider


@pytest.mark.asyncio
async def test_direct_fallback_runs_when_primary_returns_too_few_results() -> None:
    primary = FakeSearchProvider(provider_name="paper_search_mcp", titles=["one"])
    pubmed = FakeSearchProvider(provider_name="pubmed", titles=["two"])
    europe = FakeSearchProvider(provider_name="europe_pmc", titles=["three"])

    result = await SearchCandidatesUseCase(
        primary_provider=primary,
        fallback_providers=(pubmed, europe),
        fallback_threshold=5,
        max_results_per_provider_query=5,
        max_candidates_after_normalization=20,
        max_concurrent_provider_searches=4,
    ).execute(QueryPlan(queries=(RetrievalQuery(QueryIntent("global"), "sleep"),)))

    assert result.fallback_used is True
    assert [failure.provider_name for failure in result.provider_failures] == []
    assert {candidate.provider_name for candidate in result.candidates} == {
        "paper_search_mcp",
        "pubmed",
        "europe_pmc",
    }


@pytest.mark.asyncio
async def test_direct_provider_failure_is_reported_without_poisoning_successes() -> None:
    primary = FakeSearchProvider(provider_name="paper_search_mcp", fail=True)
    pubmed = FakeSearchProvider(provider_name="pubmed", titles=["two"])
    arxiv = FakeSearchProvider(provider_name="arxiv", fail=True)

    result = await SearchCandidatesUseCase(
        primary_provider=primary,
        fallback_providers=(pubmed, arxiv),
        fallback_threshold=5,
        max_results_per_provider_query=5,
        max_candidates_after_normalization=20,
        max_concurrent_provider_searches=4,
    ).execute(QueryPlan(queries=(RetrievalQuery(QueryIntent("global"), "sleep"),)))

    assert [candidate.provider_name for candidate in result.candidates] == ["pubmed"]
    assert [failure.provider_name for failure in result.provider_failures] == [
        "paper_search_mcp",
        "arxiv",
    ]
