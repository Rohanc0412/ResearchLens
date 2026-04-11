from xml.etree import ElementTree

from researchlens.modules.retrieval.domain.candidate import (
    CanonicalIdentifiers,
    NormalizedSearchCandidate,
)
from researchlens.modules.retrieval.domain.query_plan import RetrievalQuery
from researchlens.modules.retrieval.infrastructure.providers.http_mapper_primitives import (
    candidate as _candidate,
)
from researchlens.modules.retrieval.infrastructure.providers.http_mapper_primitives import (
    clean_doi as _clean_doi,
)
from researchlens.modules.retrieval.infrastructure.providers.http_mapper_primitives import (
    element_text as _element_text,
)
from researchlens.modules.retrieval.infrastructure.providers.http_mapper_primitives import (
    integer as _int,
)
from researchlens.modules.retrieval.infrastructure.providers.http_mapper_primitives import (
    string as _string,
)
from researchlens.modules.retrieval.infrastructure.providers.http_mapper_primitives import (
    strings as _strings,
)
from researchlens.modules.retrieval.infrastructure.providers.http_mapper_primitives import (
    year as _year,
)


def pubmed_candidates(
    data: dict[str, object],
    query: RetrievalQuery,
) -> list[NormalizedSearchCandidate]:
    result = data.get("result")
    raw_search = data.get("esearchresult")
    id_list = raw_search.get("idlist") if isinstance(raw_search, dict) else []
    if not isinstance(result, dict) or not isinstance(id_list, list):
        return []
    return [
        _pubmed_candidate(str(uid), row, query)
        for uid in id_list
        if isinstance(row := result.get(str(uid)), dict)
    ]


def openalex_candidates(
    data: dict[str, object],
    query: RetrievalQuery,
) -> list[NormalizedSearchCandidate]:
    rows = data.get("results")
    if not isinstance(rows, list):
        return []
    return [_openalex_candidate(row, query) for row in rows if isinstance(row, dict)]


def arxiv_candidates(xml: str, query: RetrievalQuery) -> list[NormalizedSearchCandidate]:
    root = ElementTree.fromstring(xml)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    return [_arxiv_candidate(entry, query, ns) for entry in root.findall("atom:entry", ns)]


def europe_pmc_candidates(
    data: dict[str, object],
    query: RetrievalQuery,
) -> list[NormalizedSearchCandidate]:
    result = data.get("resultList")
    rows = result.get("result") if isinstance(result, dict) else []
    if not isinstance(rows, list):
        return []
    return [_europe_pmc_candidate(row, query) for row in rows if isinstance(row, dict)]


def paper_search_mcp_candidates(
    data: dict[str, object],
    query: RetrievalQuery,
) -> list[NormalizedSearchCandidate]:
    rows = data.get("results")
    if not isinstance(rows, list):
        return []
    return [_paper_search_candidate(row, query) for row in rows if isinstance(row, dict)]


def _pubmed_candidate(
    uid: str,
    row: dict[str, object],
    query: RetrievalQuery,
) -> NormalizedSearchCandidate:
    identifiers = _pubmed_identifiers(uid, row.get("articleids"))
    return _candidate(
        provider_name="pubmed",
        provider_record_id=uid,
        identifiers=identifiers,
        title=_string(row.get("title")),
        authors=(),
        year=_year(_string(row.get("sortpubdate"))),
        source_type="paper",
        abstract=_string(row.get("abstract")),
        full_text=None,
        landing_page_url=f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
        pdf_url=None,
        venue=_string(row.get("fulljournalname")),
        citation_count=None,
        keywords=(),
        query=query,
        metadata=row,
    )


def _openalex_candidate(row: dict[str, object], query: RetrievalQuery) -> NormalizedSearchCandidate:
    raw_id = _string(row.get("id"))
    openalex_id = raw_id.rsplit("/", 1)[-1] if raw_id else None
    return _candidate(
        provider_name="openalex",
        provider_record_id=openalex_id,
        identifiers=CanonicalIdentifiers(
            doi=_clean_doi(_string(row.get("doi"))),
            openalex_id=openalex_id,
            url=raw_id,
        ),
        title=_string(row.get("title")),
        authors=(),
        year=_int(row.get("publication_year")),
        source_type="paper",
        abstract=_string(row.get("abstract")),
        full_text=None,
        landing_page_url=raw_id,
        pdf_url=None,
        venue=None,
        citation_count=_int(row.get("cited_by_count")),
        keywords=(),
        query=query,
        metadata=row,
    )


def _arxiv_candidate(
    entry: ElementTree.Element,
    query: RetrievalQuery,
    ns: dict[str, str],
) -> NormalizedSearchCandidate:
    raw_id = _element_text(entry, "atom:id", ns)
    arxiv_id = raw_id.rsplit("/", 1)[-1].removesuffix("v1") if raw_id else None
    pdf_url = None
    for link in entry.findall("atom:link", ns):
        if link.attrib.get("title") == "pdf":
            pdf_url = link.attrib.get("href")
    return _candidate(
        provider_name="arxiv",
        provider_record_id=arxiv_id,
        identifiers=CanonicalIdentifiers(arxiv_id=arxiv_id, url=raw_id),
        title=_element_text(entry, "atom:title", ns),
        authors=tuple(
            name.text.strip()
            for name in entry.findall("atom:author/atom:name", ns)
            if name.text and name.text.strip()
        ),
        year=_year(_element_text(entry, "atom:published", ns)),
        source_type="preprint",
        abstract=_element_text(entry, "atom:summary", ns),
        full_text=None,
        landing_page_url=raw_id,
        pdf_url=pdf_url,
        venue="arXiv",
        citation_count=None,
        keywords=(),
        query=query,
        metadata={},
    )


def _europe_pmc_candidate(
    row: dict[str, object],
    query: RetrievalQuery,
) -> NormalizedSearchCandidate:
    source_id = _string(row.get("id"))
    author_string = _string(row.get("authorString"))
    return _candidate(
        provider_name="europe_pmc",
        provider_record_id=source_id,
        identifiers=CanonicalIdentifiers(
            doi=_string(row.get("doi")),
            pmid=_string(row.get("pmid")),
            pmcid=_string(row.get("pmcid")),
            url=_string(row.get("fullTextUrl")),
        ),
        title=_string(row.get("title")),
        authors=tuple(author_string.split(", ")) if author_string else (),
        year=_int(row.get("pubYear")),
        source_type="paper",
        abstract=_string(row.get("abstractText")),
        full_text=_string(row.get("fullText")),
        landing_page_url=_string(row.get("fullTextUrl")),
        pdf_url=None,
        venue=_string(row.get("journalTitle")),
        citation_count=_int(row.get("citedByCount")),
        keywords=(),
        query=query,
        metadata=row,
    )


def _paper_search_candidate(
    row: dict[str, object],
    query: RetrievalQuery,
) -> NormalizedSearchCandidate:
    record_id = _string(row.get("id"))
    authors = row.get("authors")
    keywords = row.get("keywords")
    return _candidate(
        provider_name="paper_search_mcp",
        provider_record_id=record_id,
        identifiers=CanonicalIdentifiers(
            doi=_string(row.get("doi")),
            pmid=_string(row.get("pmid")),
            pmcid=_string(row.get("pmcid")),
            arxiv_id=_string(row.get("arxiv_id")),
            openalex_id=_string(row.get("openalex_id")),
            url=_string(row.get("url")),
        ),
        title=_string(row.get("title")),
        authors=tuple(item for item in authors if isinstance(item, str))
        if isinstance(authors, list)
        else (),
        year=_int(row.get("year")),
        source_type=_string(row.get("source_type")) or "paper",
        abstract=_string(row.get("abstract")),
        full_text=_string(row.get("full_text")),
        landing_page_url=_string(row.get("landing_page_url")),
        pdf_url=_string(row.get("pdf_url")),
        venue=_string(row.get("venue")),
        citation_count=_int(row.get("citation_count")),
        keywords=_strings(keywords),
        query=query,
        metadata=row,
    )


def _pubmed_identifiers(uid: str, raw_ids: object) -> CanonicalIdentifiers:
    doi = pmcid = None
    if isinstance(raw_ids, list):
        for item in raw_ids:
            if not isinstance(item, dict):
                continue
            if item.get("idtype") == "doi":
                doi = _string(item.get("value"))
            if item.get("idtype") in {"pmc", "pmcid"}:
                pmcid = _string(item.get("value"))
    return CanonicalIdentifiers(doi=doi, pmid=uid, pmcid=pmcid)
