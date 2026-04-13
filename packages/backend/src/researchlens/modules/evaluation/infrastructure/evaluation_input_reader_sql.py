from typing import cast
from uuid import UUID

from sqlalchemy import Table, select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.evaluation.application.dtos import (
    EvaluationEvidenceInput,
    EvaluationRunInput,
    EvaluationSectionInput,
)
from researchlens.shared.db import metadata
from researchlens.shared.errors import NotFoundError, ValidationError


class SqlAlchemyEvaluationInputReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load_run_evaluation_input(
        self,
        *,
        run_id: UUID,
        section_ids: tuple[str, ...] | None = None,
    ) -> EvaluationRunInput:
        runs = _table("runs")
        result = await self._session.execute(select(runs).where(runs.c.id == run_id))
        run = result.mappings().first()
        if run is None:
            raise NotFoundError(f"Run {run_id} was not found.")
        sections = await self._load_sections(run_id=run_id, section_ids=section_ids)
        if not sections:
            raise ValidationError("Evaluation requires persisted drafted sections.")
        question = await self._request_text_for_run(run_id=run_id)
        return EvaluationRunInput(
            tenant_id=cast(UUID, run["tenant_id"]),
            run_id=cast(UUID, run["id"]),
            research_question=question,
            sections=tuple(sections),
        )

    async def _load_sections(
        self,
        *,
        run_id: UUID,
        section_ids: tuple[str, ...] | None,
    ) -> list[EvaluationSectionInput]:
        sections_table = _table("drafting_sections")
        drafts_table = _table("drafting_section_drafts")
        query = (
            select(
                sections_table.c.id.label("section_row_id"),
                sections_table.c.section_id,
                sections_table.c.title,
                sections_table.c.section_order,
                drafts_table.c.section_text,
            )
            .join(
                drafts_table,
                (drafts_table.c.run_id == sections_table.c.run_id)
                & (drafts_table.c.section_id == sections_table.c.section_id),
            )
            .where(sections_table.c.run_id == run_id)
            .order_by(
                sections_table.c.section_order.asc(),
                sections_table.c.section_id.asc(),
            )
        )
        if section_ids is not None:
            query = query.where(sections_table.c.section_id.in_(section_ids))
        rows = (await self._session.execute(query)).mappings().all()
        sections: list[EvaluationSectionInput] = []
        for row in rows:
            evidence = await self._load_evidence(section_row_id=cast(UUID, row["section_row_id"]))
            repair_result_id = await self._latest_repair_result_id(
                run_id=run_id,
                section_id=cast(str, row["section_id"]),
            )
            sections.append(
                EvaluationSectionInput(
                    section_id=cast(str, row["section_id"]),
                    section_title=cast(str, row["title"]),
                    section_order=cast(int, row["section_order"]),
                    section_text=cast(str, row["section_text"]),
                    allowed_evidence=evidence,
                    repair_result_id=repair_result_id,
                )
            )
        return sections

    async def _latest_repair_result_id(
        self,
        *,
        run_id: UUID,
        section_id: str,
    ) -> UUID | None:
        repair_results = metadata.tables.get("repair_results")
        if repair_results is None:
            return None
        return cast(
            UUID | None,
            await self._session.scalar(
                select(repair_results.c.id)
                .where(
                    repair_results.c.run_id == run_id,
                    repair_results.c.section_id == section_id,
                    repair_results.c.changed.is_(True),
                )
                .order_by(repair_results.c.completed_at.desc(), repair_results.c.id.desc())
                .limit(1)
            ),
        )

    async def _load_evidence(self, *, section_row_id: UUID) -> tuple[EvaluationEvidenceInput, ...]:
        rows = (
            await self._session.execute(
                select(_table("drafting_section_evidence"))
                .where(_table("drafting_section_evidence").c.section_row_id == section_row_id)
                .order_by(
                    _table("drafting_section_evidence").c.source_rank.asc(),
                    _table("drafting_section_evidence").c.chunk_index.asc(),
                    _table("drafting_section_evidence").c.chunk_id.asc(),
                )
            )
        ).mappings().all()
        return tuple(
            EvaluationEvidenceInput(
                chunk_id=cast(UUID, row["chunk_id"]),
                source_id=cast(UUID, row["source_id"]),
                source_title=cast(str, row["source_title"]),
                source_rank=cast(int, row["source_rank"]),
                chunk_index=cast(int, row["chunk_index"]),
                text=cast(str, row["excerpt_text"]),
            )
            for row in rows
        )

    async def _request_text_for_run(self, *, run_id: UUID) -> str:
        events_table = _table("run_events")
        result = await self._session.execute(
            select(events_table.c.payload_json)
            .where(events_table.c.run_id == run_id, events_table.c.event_type == "run.created")
            .order_by(events_table.c.event_number.asc())
            .limit(1)
        )
        payload = result.scalar_one_or_none()
        if isinstance(payload, dict):
            request_text = payload.get("request_text")
            if isinstance(request_text, str) and request_text.strip():
                return request_text.strip()
        return f"Research report {cast(object, run_id)}"


def _table(name: str) -> Table:
    return metadata.tables[name]
