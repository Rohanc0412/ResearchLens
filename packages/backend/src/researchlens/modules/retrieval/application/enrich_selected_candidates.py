import asyncio
from dataclasses import replace

from researchlens.modules.retrieval.application.ports import SearchProvider
from researchlens.modules.retrieval.domain.candidate import NormalizedSearchCandidate


class EnrichmentRouter:
    def __init__(self, providers: dict[str, SearchProvider]) -> None:
        self._providers = providers

    def route(self, candidate: NormalizedSearchCandidate) -> SearchProvider:
        identifiers = candidate.identifiers.normalized()
        if identifiers.pmid and "pubmed" in self._providers:
            return self._providers["pubmed"]
        if identifiers.pmcid and "europe_pmc" in self._providers:
            return self._providers["europe_pmc"]
        if identifiers.arxiv_id and "arxiv" in self._providers:
            return self._providers["arxiv"]
        return self._providers["openalex"]


async def enrich_candidates(
    candidates: list[NormalizedSearchCandidate],
    *,
    router: EnrichmentRouter,
    max_concurrent_fetches: int,
) -> list[NormalizedSearchCandidate]:
    limiter = asyncio.Semaphore(max_concurrent_fetches)

    async def fetch(candidate: NormalizedSearchCandidate) -> NormalizedSearchCandidate:
        async with limiter:
            content = await router.route(candidate).fetch_content(candidate)
        if content is None:
            return candidate
        return replace(
            candidate,
            full_text=content.full_text or candidate.full_text,
            abstract=content.abstract or candidate.abstract,
            landing_page_url=content.landing_page_url or candidate.landing_page_url,
            pdf_url=content.pdf_url or candidate.pdf_url,
        )

    return list(await asyncio.gather(*(fetch(candidate) for candidate in candidates)))
