from typing import cast
from uuid import UUID

from sqlalchemy import Table, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.drafting.application.dto import (
    EvidenceRecord,
    RunDraftingInput,
    SectionPlanRecord,
)
from researchlens.modules.drafting.application.ports import DraftingRunInputReader
from researchlens.shared.db import metadata
from researchlens.shared.errors import NotFoundError


class SqlAlchemyDraftingRunInputReader(DraftingRunInputReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load_run_drafting_input(self, *, run_id: UUID) -> RunDraftingInput:
        run_data = await self._load_run_row(run_id=run_id)
        request_text = await self._run_request_text(run_id=run_id)
        sections = await self._derive_sections(run_id=run_id)
        evidence = await self._load_evidence(run_id=run_id)
        return RunDraftingInput(
            tenant_id=cast(UUID, run_data["tenant_id"]),
            run_id=cast(UUID, run_data["id"]),
            report_title=request_text[:240],
            research_question=request_text,
            sections=sections,
            evidence=evidence,
        )

    async def _load_run_row(self, *, run_id: UUID) -> dict[str, object]:
        runs_table = _table("runs")
        result = await self._session.execute(
            select(
                runs_table.c.tenant_id,
                runs_table.c.id,
                runs_table.c.output_type,
            ).where(runs_table.c.id == run_id)
        )
        run_data = result.mappings().first()
        if run_data is None:
            raise NotFoundError(f"Run {run_id} was not found.")
        return dict(run_data)

    async def _run_request_text(self, *, run_id: UUID) -> str:
        run_events_table = _table("run_events")
        result = await self._session.execute(
            select(run_events_table.c.payload_json)
            .where(
                run_events_table.c.run_id == run_id,
                run_events_table.c.event_type == "run.created",
            )
            .order_by(run_events_table.c.event_number.asc())
            .limit(1)
        )
        payload = result.scalar_one_or_none() or {}
        if isinstance(payload, dict):
            request_text = payload.get("request_text")
            if isinstance(request_text, str) and request_text.strip():
                return request_text.strip()
        return f"Research report {run_id}"

    async def _derive_sections(self, *, run_id: UUID) -> tuple[SectionPlanRecord, ...]:
        run_retrieval_sources = _table("run_retrieval_sources")
        section_expr = func.coalesce(run_retrieval_sources.c.target_section, "overview")
        result = await self._session.execute(
            select(
                section_expr.label("section_id"),
                func.min(run_retrieval_sources.c.rank).label("first_rank"),
            )
            .where(run_retrieval_sources.c.run_id == run_id)
            .group_by(section_expr)
            .order_by(
                case((section_expr == "overview", 0), else_=1),
                func.min(run_retrieval_sources.c.rank),
                section_expr,
            )
        )
        sections = []
        for order, row in enumerate(result.mappings().all(), start=1):
            section_id = row["section_id"]
            title = " ".join(str(section_id).replace("_", " ").replace("-", " ").split()).title()
            sections.append(
                SectionPlanRecord(
                    section_id=section_id,
                    title=title,
                    section_order=order,
                    goal=f"Draft the {title} section using only its allowed evidence.",
                    key_points=(),
                )
            )
        return tuple(sections)

    async def _load_evidence(self, *, run_id: UUID) -> tuple[EvidenceRecord, ...]:
        runs_table = _table("runs")
        retrieval_sources = _table("retrieval_sources")
        retrieval_snapshots = _table("retrieval_source_snapshots")
        retrieval_chunks = _table("retrieval_source_chunks")
        run_retrieval_sources = _table("run_retrieval_sources")
        result = await self._session.execute(
            select(
                run_retrieval_sources.c.run_id,
                runs_table.c.tenant_id,
                run_retrieval_sources.c.source_id,
                retrieval_chunks.c.id.label("chunk_id"),
                run_retrieval_sources.c.rank.label("source_rank"),
                retrieval_chunks.c.chunk_index,
                run_retrieval_sources.c.target_section,
                func.coalesce(retrieval_sources.c.title, "Untitled source").label(
                    "source_title"
                ),
                retrieval_chunks.c.text.label("chunk_text"),
            )
            .select_from(run_retrieval_sources)
            .join(runs_table, runs_table.c.id == run_retrieval_sources.c.run_id)
            .join(retrieval_sources, retrieval_sources.c.id == run_retrieval_sources.c.source_id)
            .join(retrieval_snapshots, retrieval_snapshots.c.source_id == retrieval_sources.c.id)
            .join(retrieval_chunks, retrieval_chunks.c.snapshot_id == retrieval_snapshots.c.id)
            .where(run_retrieval_sources.c.run_id == run_id)
            .order_by(
                run_retrieval_sources.c.rank.asc(),
                retrieval_chunks.c.chunk_index.asc(),
                retrieval_chunks.c.id.asc(),
            )
        )
        return tuple(EvidenceRecord.model_validate(row) for row in result.mappings().all())


def _table(name: str) -> Table:
    return metadata.tables[name]
