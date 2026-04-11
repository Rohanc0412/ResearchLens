from datetime import UTC, datetime

import pytest

from researchlens.modules.retrieval.application.enrich_selected_candidates import (
    EnrichmentRouter,
    enrich_candidates,
)
from researchlens.modules.retrieval.application.rerank_with_embeddings import (
    EmbeddingReranker,
)
from researchlens.modules.retrieval.domain.candidate import (
    CanonicalIdentifiers,
    NormalizedSearchCandidate,
    QueryProvenance,
    SourceProvenance,
)
from researchlens.modules.retrieval.domain.ranking_policy import RankingWeights, rank_candidates
from researchlens.modules.retrieval.infrastructure.providers.fake_provider import FakeSearchProvider
from researchlens.shared.embeddings.domain import EmbeddingRequest, EmbeddingResult


class FakeEmbeddingClient:
    model = "text-embedding-3-small"

    def __init__(self) -> None:
        self.requests: list[EmbeddingRequest] = []

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        self.requests.append(request)
        return EmbeddingResult(vectors=tuple((float(len(text)),) for text in request.texts))


@pytest.mark.asyncio
async def test_targeted_enrichment_routes_by_identifier() -> None:
    router = EnrichmentRouter(
        providers={
            "pubmed": FakeSearchProvider(provider_name="pubmed", titles=[]),
            "europe_pmc": FakeSearchProvider(provider_name="europe_pmc", titles=[]),
            "arxiv": FakeSearchProvider(provider_name="arxiv", titles=[]),
            "openalex": FakeSearchProvider(provider_name="openalex", titles=[]),
        }
    )

    assert router.route(_candidate(pmid="1")).provider_name == "pubmed"
    assert router.route(_candidate(pmcid="PMC1")).provider_name == "europe_pmc"
    assert router.route(_candidate(arxiv_id="2401.1")).provider_name == "arxiv"
    assert router.route(_candidate()).provider_name == "openalex"


@pytest.mark.asyncio
async def test_enrichment_fetches_selected_candidates_concurrently() -> None:
    provider = FakeSearchProvider(provider_name="openalex", titles=[])
    enriched = await enrich_candidates(
        [_candidate(title="One"), _candidate(title="Two")],
        router=EnrichmentRouter(providers={"openalex": provider}),
        max_concurrent_fetches=2,
    )

    assert [item.title for item in enriched] == ["One", "Two"]


@pytest.mark.asyncio
async def test_embedding_reranker_batches_top_k_texts() -> None:
    client = FakeEmbeddingClient()
    candidate = _candidate(title="Sleep memory", abstract="Sleep improves memory")
    ranked = rank_candidates(
        candidates=[candidate],
        queries=[],
        weights=RankingWeights(lexical=1, embedding=0, recency=0, citation=0),
        embedding_scores={},
    )

    scores = await EmbeddingReranker(
        client=client,
        batch_size=8,
        max_concurrent_batches=2,
    ).score_top_k(ranked, top_k=1, query_text="sleep memory")

    assert list(scores.values()) == [1.0]
    assert client.requests[0].texts == ("sleep memory", "Sleep memory\nSleep improves memory")


def _candidate(
    *,
    title: str = "Paper",
    abstract: str = "Abstract",
    pmid: str | None = None,
    pmcid: str | None = None,
    arxiv_id: str | None = None,
) -> NormalizedSearchCandidate:
    return NormalizedSearchCandidate(
        provider_name="test",
        provider_record_id="1",
        identifiers=CanonicalIdentifiers(pmid=pmid, pmcid=pmcid, arxiv_id=arxiv_id),
        title=title,
        authors=(),
        year=None,
        source_type="paper",
        abstract=abstract,
        full_text=None,
        landing_page_url=None,
        pdf_url=None,
        venue=None,
        citation_count=None,
        keywords=(),
        retrieved_at=datetime.now(tz=UTC),
        provider_metadata={},
        provenance=(SourceProvenance("test", "1"),),
        query_provenance=QueryProvenance("q", "global"),
    )
