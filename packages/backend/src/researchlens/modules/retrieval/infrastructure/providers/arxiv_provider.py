import httpx

from researchlens.modules.retrieval.application.ports import (
    FetchedSourceContent,
    ProviderSearchRequest,
)
from researchlens.modules.retrieval.domain.candidate import NormalizedSearchCandidate
from researchlens.modules.retrieval.infrastructure.providers.http_mappers import arxiv_candidates


class ArxivProvider:
    provider_name = "arxiv"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(
            base_url="https://export.arxiv.org",
            timeout=20.0,
        )

    async def search(self, request: ProviderSearchRequest) -> list[NormalizedSearchCandidate]:
        response = await self._client.get(
            "/api/query",
            params={
                "search_query": f"all:{request.query.query}",
                "start": 0,
                "max_results": request.max_results,
            },
        )
        response.raise_for_status()
        return arxiv_candidates(response.text, request.query)

    async def fetch_content(
        self,
        candidate: NormalizedSearchCandidate,
    ) -> FetchedSourceContent | None:
        return FetchedSourceContent(
            full_text=candidate.full_text,
            abstract=candidate.abstract,
            landing_page_url=candidate.landing_page_url,
            pdf_url=candidate.pdf_url,
        )
