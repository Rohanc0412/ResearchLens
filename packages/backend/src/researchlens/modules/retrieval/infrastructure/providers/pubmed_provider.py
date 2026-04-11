import httpx

from researchlens.modules.retrieval.application.ports import (
    FetchedSourceContent,
    ProviderSearchRequest,
)
from researchlens.modules.retrieval.domain.candidate import NormalizedSearchCandidate
from researchlens.modules.retrieval.infrastructure.providers.http_mappers import pubmed_candidates


class PubMedProvider:
    provider_name = "pubmed"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(
            base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            timeout=20.0,
        )

    async def search(self, request: ProviderSearchRequest) -> list[NormalizedSearchCandidate]:
        response = await self._client.get(
            "/esummary.fcgi",
            params={
                "db": "pubmed",
                "retmode": "json",
                "term": request.query.query,
                "retmax": request.max_results,
            },
        )
        response.raise_for_status()
        return pubmed_candidates(response.json(), request.query)

    async def fetch_content(
        self,
        candidate: NormalizedSearchCandidate,
    ) -> FetchedSourceContent | None:
        return FetchedSourceContent(
            full_text=None,
            abstract=candidate.abstract,
            landing_page_url=candidate.landing_page_url,
            pdf_url=candidate.pdf_url,
        )
