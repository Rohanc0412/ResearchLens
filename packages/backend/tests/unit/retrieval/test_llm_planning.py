import pytest

from researchlens.modules.retrieval.application.generate_retrieval_outline import (
    GenerateRetrievalOutlineUseCase,
)
from researchlens.modules.retrieval.application.plan_queries_from_outline import (
    LlmQueryPlanner,
)
from researchlens.shared.llm.domain import StructuredGenerationRequest, StructuredGenerationResult


class FakeLlm:
    model = "gpt-5-nano"

    def __init__(self, data: dict[str, object], *, fail: bool = False) -> None:
        self.data = data
        self.fail = fail
        self.requests: list[StructuredGenerationRequest] = []

    async def generate_structured(
        self,
        request: StructuredGenerationRequest,
    ) -> StructuredGenerationResult:
        self.requests.append(request)
        if self.fail:
            raise RuntimeError("llm failed")
        return StructuredGenerationResult(data=self.data)


@pytest.mark.asyncio
async def test_llm_outline_generation_validates_structured_output() -> None:
    llm = FakeLlm(
        {
            "report_title": "Sleep and memory",
            "sections": [
                {
                    "section_id": "mechanisms",
                    "title": "Mechanisms",
                    "goal": "Find mechanism evidence",
                    "suggested_evidence_themes": ["REM sleep", "hippocampus"],
                    "key_points": ["memory consolidation"],
                    "section_order": 1,
                }
            ],
        }
    )

    outline = await GenerateRetrievalOutlineUseCase(llm, max_sections=3).execute(
        "How does sleep affect memory?"
    )

    assert outline.report_title == "Sleep and memory"
    assert outline.sections[0].section_id == "mechanisms"
    assert llm.requests[0].schema_name == "retrieval_outline"


@pytest.mark.asyncio
async def test_llm_query_planning_falls_back_to_deterministic_plan_on_failure() -> None:
    outline = await GenerateRetrievalOutlineUseCase(
        FakeLlm(
            {
                "report_title": "Sleep",
                "sections": [
                    {
                        "section_id": "overview",
                        "title": "Overview",
                        "goal": "Find evidence",
                        "suggested_evidence_themes": ["sleep memory"],
                        "section_order": 1,
                    }
                ],
            }
        ),
        max_sections=3,
    ).execute("sleep memory")

    planner = LlmQueryPlanner(
        FakeLlm({}, fail=True),
        max_global_queries=1,
        max_queries_per_section=1,
    )

    plan = await planner.plan(question="sleep memory", outline=outline)

    assert [query.intent.value for query in plan.queries] == ["global", "overview"]


@pytest.mark.asyncio
async def test_llm_query_planning_deduplicates_structured_outputs() -> None:
    outline = await GenerateRetrievalOutlineUseCase(
        FakeLlm(
            {
                "report_title": "Sleep",
                "sections": [
                    {
                        "section_id": "overview",
                        "title": "Overview",
                        "goal": "Find evidence",
                        "suggested_evidence_themes": ["sleep memory"],
                        "section_order": 1,
                    }
                ],
            }
        ),
        max_sections=3,
    ).execute("sleep memory")
    planner = LlmQueryPlanner(
        FakeLlm(
            {
                "queries": [
                    {"intent": "global", "query": "sleep memory"},
                    {"intent": "global", "query": " sleep memory "},
                    {
                        "intent": "overview",
                        "query": "REM sleep hippocampus",
                        "target_section": "overview",
                    },
                ]
            }
        ),
        max_global_queries=3,
        max_queries_per_section=2,
    )

    plan = await planner.plan(question="sleep memory", outline=outline)

    assert [query.query for query in plan.queries] == [
        "sleep memory",
        "REM sleep hippocampus",
    ]
