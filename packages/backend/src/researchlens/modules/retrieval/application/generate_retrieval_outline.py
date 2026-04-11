from typing import Any

from researchlens.modules.retrieval.domain.retrieval_outline import (
    RetrievalOutline,
    RetrievalOutlineSection,
)
from researchlens.shared.llm.domain import StructuredGenerationRequest
from researchlens.shared.llm.ports import StructuredGenerationClient


class GenerateRetrievalOutlineUseCase:
    def __init__(self, llm: StructuredGenerationClient, *, max_sections: int) -> None:
        self._llm = llm
        self._max_sections = max_sections

    async def execute(self, question: str) -> RetrievalOutline:
        result = await self._llm.generate_structured(
            StructuredGenerationRequest(
                schema_name="retrieval_outline",
                system_prompt=(
                    "Create a bounded retrieval-focused report outline. "
                    "Do not draft prose or conclusions."
                ),
                prompt=(
                    f"Research question: {question}\n"
                    f"Return at most {self._max_sections} sections with ids, titles, "
                    "goals, suggested evidence themes, optional key points, and order."
                ),
            )
        )
        return _outline_from_data(result.data, max_sections=self._max_sections)


def _outline_from_data(data: dict[str, Any], *, max_sections: int) -> RetrievalOutline:
    sections = []
    for index, raw_section in enumerate(data.get("sections", [])[:max_sections], start=1):
        if not isinstance(raw_section, dict):
            continue
        section_id = _text(raw_section.get("section_id")) or f"section-{index}"
        title = _text(raw_section.get("title")) or section_id.replace("-", " ").title()
        sections.append(
            RetrievalOutlineSection(
                section_id=section_id,
                title=title,
                goal=_text(raw_section.get("goal")) or f"Find evidence for {title}.",
                suggested_evidence_themes=tuple(
                    _iter_text(raw_section.get("suggested_evidence_themes"))
                ),
                key_points=tuple(_iter_text(raw_section.get("key_points"))),
                section_order=int(raw_section.get("section_order") or index),
            )
        )
    return RetrievalOutline(
        report_title=_text(data.get("report_title")) or "ResearchLens retrieval outline",
        sections=tuple(sections),
    )


def deterministic_retrieval_outline(question: str) -> RetrievalOutline:
    return RetrievalOutline(
        report_title=question[:120] or "ResearchLens retrieval",
        sections=(
            RetrievalOutlineSection(
                section_id="overview",
                title="Overview",
                goal="Find high quality sources for the research question.",
                suggested_evidence_themes=(question,),
                key_points=(),
                section_order=1,
            ),
        ),
    )


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _iter_text(value: object) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]
