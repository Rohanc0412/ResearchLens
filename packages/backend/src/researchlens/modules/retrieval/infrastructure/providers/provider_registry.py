from researchlens.modules.retrieval.application.ports import SearchProvider
from researchlens.modules.retrieval.infrastructure.providers.arxiv_provider import ArxivProvider
from researchlens.modules.retrieval.infrastructure.providers.europe_pmc_provider import (
    EuropePmcProvider,
)
from researchlens.modules.retrieval.infrastructure.providers.fake_provider import FakeSearchProvider
from researchlens.modules.retrieval.infrastructure.providers.openalex_provider import (
    OpenAlexProvider,
)
from researchlens.modules.retrieval.infrastructure.providers.paper_search_mcp_provider import (
    PaperSearchMcpProvider,
)
from researchlens.modules.retrieval.infrastructure.providers.pubmed_provider import PubMedProvider
from researchlens.shared.config.retrieval import RetrievalSettings


def build_provider_registry(settings: RetrievalSettings) -> dict[str, SearchProvider]:
    if not settings.allow_external_fetch:
        return _offline_provider_registry(settings)
    available: dict[str, SearchProvider] = {
        "paper_search_mcp": PaperSearchMcpProvider(),
        "pubmed": PubMedProvider(),
        "europe_pmc": EuropePmcProvider(),
        "openalex": OpenAlexProvider(),
        "arxiv": ArxivProvider(),
    }
    return {
        name: provider
        for name, provider in available.items()
        if name in settings.enabled_providers
    }


def _offline_provider_registry(settings: RetrievalSettings) -> dict[str, SearchProvider]:
    available: dict[str, SearchProvider] = {
        "paper_search_mcp": FakeSearchProvider(
            provider_name="paper_search_mcp",
            titles=[
                "Primary retrieval candidate one",
                "Primary retrieval candidate two",
                "Primary retrieval candidate three",
                "Primary retrieval candidate four",
                "Primary retrieval candidate five",
            ],
        ),
        "pubmed": FakeSearchProvider(provider_name="pubmed", titles=["PubMed retrieval candidate"]),
        "europe_pmc": FakeSearchProvider(
            provider_name="europe_pmc",
            titles=["Europe PMC retrieval candidate"],
        ),
        "openalex": FakeSearchProvider(
            provider_name="openalex",
            titles=["OpenAlex retrieval candidate"],
        ),
        "arxiv": FakeSearchProvider(provider_name="arxiv", titles=["arXiv retrieval candidate"]),
    }
    return {
        name: provider
        for name, provider in available.items()
        if name in settings.enabled_providers
    }
