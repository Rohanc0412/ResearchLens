import httpx
import pytest

from researchlens.modules.retrieval.application.ports import ProviderSearchRequest
from researchlens.modules.retrieval.domain.query_plan import QueryIntent, RetrievalQuery
from researchlens.modules.retrieval.infrastructure.providers.arxiv_provider import ArxivProvider
from researchlens.modules.retrieval.infrastructure.providers.openalex_provider import (
    OpenAlexProvider,
)
from researchlens.modules.retrieval.infrastructure.providers.paper_search_mcp_provider import (
    PaperSearchMcpProvider,
)
from researchlens.modules.retrieval.infrastructure.providers.pubmed_provider import PubMedProvider


@pytest.mark.asyncio
async def test_pubmed_adapter_maps_identifiers_from_fixture_response() -> None:
    provider = PubMedProvider(
        client=_json_client(
            {
                "esearchresult": {"idlist": ["123"]},
                "result": {
                    "123": {
                        "uid": "123",
                        "title": "Biomedical paper",
                        "sortpubdate": "2024/01/01",
                        "articleids": [
                            {"idtype": "doi", "value": "10.1/example"},
                            {"idtype": "pmc", "value": "PMC123"},
                        ],
                    }
                },
            }
        )
    )

    results = await provider.search(_request())

    assert results[0].identifiers.pmid == "123"
    assert results[0].identifiers.doi == "10.1/example"
    assert results[0].identifiers.pmcid == "PMC123"


@pytest.mark.asyncio
async def test_paper_search_mcp_adapter_maps_canonical_fields() -> None:
    provider = PaperSearchMcpProvider(
        client=_json_client(
            {
                "results": [
                    {
                        "id": "mcp-1",
                        "title": "MCP paper",
                        "doi": "10.3/example",
                        "abstract": "Abstract",
                        "year": 2025,
                        "authors": ["A. Author"],
                    }
                ]
            }
        )
    )

    results = await provider.search(_request())

    assert results[0].provider_name == "paper_search_mcp"
    assert results[0].identifiers.doi == "10.3/example"
    assert results[0].title == "MCP paper"


@pytest.mark.asyncio
async def test_openalex_adapter_maps_openalex_id_and_citation_count() -> None:
    provider = OpenAlexProvider(
        client=_json_client(
            {
                "results": [
                    {
                        "id": "https://openalex.org/W123",
                        "title": "OpenAlex paper",
                        "publication_year": 2023,
                        "doi": "https://doi.org/10.2/example",
                        "cited_by_count": 42,
                    }
                ]
            }
        )
    )

    results = await provider.search(_request())

    assert results[0].identifiers.openalex_id == "W123"
    assert results[0].citation_count == 42
    assert results[0].identifiers.doi == "10.2/example"


@pytest.mark.asyncio
async def test_arxiv_adapter_maps_atom_fixture_response() -> None:
    xml = """<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2401.00001v1</id>
        <title>arXiv paper</title>
        <summary>Abstract text</summary>
        <published>2024-01-01T00:00:00Z</published>
        <author><name>A. Author</name></author>
        <link href="http://arxiv.org/pdf/2401.00001v1" title="pdf"/>
      </entry>
    </feed>"""
    provider = ArxivProvider(client=_text_client(xml))

    results = await provider.search(_request())

    assert results[0].identifiers.arxiv_id == "2401.00001"
    assert results[0].pdf_url == "http://arxiv.org/pdf/2401.00001v1"


def _request() -> ProviderSearchRequest:
    return ProviderSearchRequest(
        query=RetrievalQuery(QueryIntent("global"), "sleep memory"),
        max_results=3,
    )


def _json_client(payload: dict[str, object]) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload)),
        base_url="https://example.test",
    )


def _text_client(payload: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text=payload)),
        base_url="https://example.test",
    )
