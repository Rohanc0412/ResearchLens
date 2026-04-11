from researchlens.modules.retrieval.domain.query_plan import QueryIntent, QueryPlan, RetrievalQuery
from researchlens.modules.retrieval.domain.retrieval_outline import RetrievalOutline
from researchlens.shared.llm.domain import StructuredGenerationRequest
from researchlens.shared.llm.ports import StructuredGenerationClient


class DeterministicQueryPlanner:
    def __init__(self, *, max_global_queries: int, max_queries_per_section: int) -> None:
        self._max_global_queries = max_global_queries
        self._max_queries_per_section = max_queries_per_section

    def plan(self, *, question: str, outline: RetrievalOutline) -> QueryPlan:
        queries: list[RetrievalQuery] = []
        for query in _dedupe([question])[: self._max_global_queries]:
            queries.append(RetrievalQuery(intent=QueryIntent("global"), query=query))
        for section in sorted(outline.sections, key=lambda item: item.section_order):
            section_queries = [
                f"{question} {section.title}",
                *[
                    f"{section.title} {theme}"
                    for theme in section.suggested_evidence_themes
                ],
            ]
            for query in _dedupe(section_queries)[: self._max_queries_per_section]:
                queries.append(
                    RetrievalQuery(
                        intent=QueryIntent(section.section_id),
                        query=query,
                        target_section=section.section_id,
                    )
                )
        return QueryPlan(queries=tuple(_dedupe_query_entries(queries)))


class LlmQueryPlanner:
    def __init__(
        self,
        llm: StructuredGenerationClient,
        *,
        max_global_queries: int,
        max_queries_per_section: int,
    ) -> None:
        self._llm = llm
        self._fallback = DeterministicQueryPlanner(
            max_global_queries=max_global_queries,
            max_queries_per_section=max_queries_per_section,
        )

    async def plan(self, *, question: str, outline: RetrievalOutline) -> QueryPlan:
        try:
            result = await self._llm.generate_structured(
                build_query_plan_request(question=question, outline=outline)
            )
            return _query_plan_from_data(result.data)
        except Exception:
            return self._fallback.plan(question=question, outline=outline)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = " ".join(value.split())
        if normalized and normalized.casefold() not in seen:
            seen.add(normalized.casefold())
            result.append(normalized)
    return result


def _dedupe_query_entries(entries: list[RetrievalQuery]) -> list[RetrievalQuery]:
    seen: set[str] = set()
    result: list[RetrievalQuery] = []
    for entry in entries:
        key = entry.query.casefold()
        if key not in seen:
            seen.add(key)
            result.append(entry)
    return result


def _query_plan_from_data(data: dict[str, object]) -> QueryPlan:
    entries: list[RetrievalQuery] = []
    raw_queries = data.get("queries")
    if not isinstance(raw_queries, list):
        return QueryPlan(queries=())
    for raw in raw_queries:
        if not isinstance(raw, dict):
            continue
        query = raw.get("query")
        intent = raw.get("intent") or "global"
        target_section = raw.get("target_section")
        if isinstance(query, str) and query.strip():
            entries.append(
                RetrievalQuery(
                    intent=QueryIntent(str(intent)),
                    query=" ".join(query.split()),
                    target_section=target_section if isinstance(target_section, str) else None,
                )
            )
    return QueryPlan(queries=tuple(_dedupe_query_entries(entries)))


def build_query_plan_request(
    *,
    question: str,
    outline: RetrievalOutline,
) -> StructuredGenerationRequest:
    return StructuredGenerationRequest(
        schema_name="retrieval_query_plan",
        system_prompt=(
            "Create retrieval search queries from the outline. "
            "Return query objects only; do not score or rank."
        ),
        prompt=_query_prompt(question=question, outline=outline),
    )


def _query_prompt(*, question: str, outline: RetrievalOutline) -> str:
    sections = [
        {
            "section_id": section.section_id,
            "title": section.title,
            "goal": section.goal,
            "themes": section.suggested_evidence_themes,
        }
        for section in outline.sections
    ]
    return f"Research question: {question}\nOutline sections: {sections}"
