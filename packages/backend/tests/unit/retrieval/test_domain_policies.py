from datetime import UTC, datetime

from researchlens.modules.retrieval.domain.candidate import (
    CanonicalIdentifiers,
    NormalizedSearchCandidate,
    QueryProvenance,
    SourceProvenance,
)
from researchlens.modules.retrieval.domain.deduplication import deduplicate_candidates
from researchlens.modules.retrieval.domain.diversification_policy import diversify_candidates
from researchlens.modules.retrieval.domain.query_plan import (
    QueryIntent,
    RetrievalQuery,
    normalize_query_intent,
)
from researchlens.modules.retrieval.domain.ranking_policy import (
    RankingWeights,
    rank_candidates,
)


def test_intent_normalization_rejects_empty_and_stabilizes_text() -> None:
    assert normalize_query_intent(" Background Evidence ") == "background-evidence"
    assert normalize_query_intent("methods/results") == "methods-results"
    assert normalize_query_intent("") == "general"


def test_deduplication_prefers_identifier_and_preserves_provenance() -> None:
    first = _candidate(
        provider="paper_search_mcp",
        title="A Trial",
        doi="10.1000/example",
        abstract=None,
    )
    second = _candidate(
        provider="pubmed",
        title="A Trial",
        doi="10.1000/EXAMPLE",
        abstract="Richer abstract",
        citation_count=20,
    )

    merged = deduplicate_candidates([first, second])

    assert len(merged) == 1
    assert merged[0].abstract == "Richer abstract"
    assert merged[0].citation_count == 20
    assert [item.provider_name for item in merged[0].provenance] == [
        "paper_search_mcp",
        "pubmed",
    ]


def test_ranking_is_deterministic_and_uses_citation_signal() -> None:
    low = _candidate(provider="pubmed", title="Cancer screening review", citation_count=1)
    high = _candidate(provider="openalex", title="Cancer screening review", citation_count=100)

    ranked = rank_candidates(
        candidates=[low, high],
        queries=[RetrievalQuery(intent=QueryIntent("general"), query="cancer screening")],
        weights=RankingWeights(lexical=1.0, embedding=0.0, recency=0.0, citation=1.0),
        embedding_scores={},
    )

    assert [item.candidate.provider_name for item in ranked] == ["openalex", "pubmed"]
    assert ranked[0].score_breakdown.citation > ranked[1].score_breakdown.citation


def test_diversification_spreads_intents_before_backfill() -> None:
    ranked = rank_candidates(
        candidates=[
            _candidate(provider="pubmed", title="alpha one", intent="alpha"),
            _candidate(provider="pubmed", title="alpha two", intent="alpha"),
            _candidate(provider="arxiv", title="beta one", intent="beta"),
        ],
        queries=[RetrievalQuery(intent=QueryIntent("alpha"), query="alpha")],
        weights=RankingWeights(lexical=1.0, embedding=0.0, recency=0.0, citation=0.0),
        embedding_scores={},
    )

    selected = diversify_candidates(ranked, max_selected=3, per_bucket_limit=1)

    assert [item.candidate.query_provenance.intent for item in selected[:2]] == ["alpha", "beta"]
    assert len(selected) == 3


def _candidate(
    *,
    provider: str,
    title: str,
    doi: str | None = None,
    abstract: str | None = "Abstract text",
    citation_count: int | None = None,
    intent: str = "general",
) -> NormalizedSearchCandidate:
    return NormalizedSearchCandidate(
        provider_name=provider,
        provider_record_id=f"{provider}-1",
        identifiers=CanonicalIdentifiers(doi=doi),
        title=title,
        authors=("A. Author",),
        year=2024,
        source_type="paper",
        abstract=abstract,
        full_text=None,
        landing_page_url=None,
        pdf_url=None,
        venue=None,
        citation_count=citation_count,
        keywords=(),
        retrieved_at=datetime.now(tz=UTC),
        provider_metadata={},
        provenance=(SourceProvenance(provider_name=provider, provider_record_id="1"),),
        query_provenance=QueryProvenance(source_query="query", intent=intent, target_section=None),
    )
