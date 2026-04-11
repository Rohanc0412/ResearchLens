import httpx

from researchlens.modules.retrieval.application.ports import (
    FetchedSourceContent,
    ProviderSearchRequest,
)
from researchlens.modules.retrieval.domain.candidate import NormalizedSearchCandidate
from researchlens.modules.retrieval.infrastructure.providers.http_mappers import (
    paper_search_mcp_candidates,
)


class PaperSearchMcpProvider:
    provider_name = "paper_search_mcp"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(
            base_url="http://localhost:8765",
            timeout=20.0,
        )

    async def search(self, request: ProviderSearchRequest) -> list[NormalizedSearchCandidate]:
        response = await self._client.post(
            "/search",
            json={"query": request.query.query, "limit": request.max_results},
        )
        response.raise_for_status()
        return paper_search_mcp_candidates(response.json(), request.query)

    async def fetch_content(
        self,
        candidate: NormalizedSearchCandidate,
    ) -> FetchedSourceContent | None:
        if candidate.provider_record_id is None:
            return None
        response = await self._client.post(
            "/fetch",
            json={"id": candidate.provider_record_id},
        )
        response.raise_for_status()
        data = response.json()
        return FetchedSourceContent(
            full_text=data.get("full_text") if isinstance(data.get("full_text"), str) else None,
            abstract=data.get("abstract") if isinstance(data.get("abstract"), str) else None,
            landing_page_url=data.get("landing_page_url")
            if isinstance(data.get("landing_page_url"), str)
            else None,
            pdf_url=data.get("pdf_url") if isinstance(data.get("pdf_url"), str) else None,
        )
