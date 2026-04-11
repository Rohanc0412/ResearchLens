import pytest

from researchlens.modules.retrieval.application.plan_queries_from_outline import (
    DeterministicQueryPlanner,
)
from researchlens.modules.retrieval.domain.retrieval_outline import (
    RetrievalOutline,
    RetrievalOutlineSection,
)
from researchlens.shared.errors import ValidationError


def test_outline_rejects_duplicate_section_ids() -> None:
    with pytest.raises(ValidationError):
        RetrievalOutline(
            report_title="Title",
            sections=(
                _section("intro", 1, "Intro"),
                _section("intro", 2, "Other"),
            ),
        )


def test_fallback_query_planner_generates_global_and_section_queries() -> None:
    planner = DeterministicQueryPlanner(max_global_queries=1, max_queries_per_section=2)

    plan = planner.plan(
        question="How does sleep affect memory consolidation?",
        outline=RetrievalOutline(
            report_title="Sleep and memory",
            sections=(
                _section("mechanisms", 1, "Mechanisms", "hippocampus REM sleep"),
                _section("clinical", 2, "Clinical evidence", "older adults trials"),
            ),
        ),
    )

    assert [entry.intent.value for entry in plan.queries] == [
        "global",
        "mechanisms",
        "mechanisms",
        "clinical",
        "clinical",
    ]
    assert len({entry.query for entry in plan.queries}) == 5


def _section(
    section_id: str,
    order: int,
    title: str,
    theme: str = "evidence",
) -> RetrievalOutlineSection:
    return RetrievalOutlineSection(
        section_id=section_id,
        title=title,
        goal=f"Find {title}",
        suggested_evidence_themes=(theme,),
        key_points=(),
        section_order=order,
    )
