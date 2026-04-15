import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.artifacts.domain.export_models import (
    ExportChunk,
    ExportSource,
    FinalSection,
    ReportExportBundle,
)
from researchlens.shared.errors import NotFoundError, ValidationError


class SqlAlchemyExportBundleReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load_bundle(self, *, run_id: UUID) -> ReportExportBundle:
        run = await self._mapping(_RUN_SQL, {"run_id": _db_uuid(run_id)})
        if run is None:
            raise NotFoundError("Run was not found for export.")
        sections = await self._sections(run_id=run_id)
        if not sections:
            raise ValidationError("Export requires persisted section drafts.")
        chunks = await self._chunks(run_id=run_id)
        sources = await self._sources(run_id=run_id)
        return ReportExportBundle(
            tenant_id=_uuid(run["tenant_id"]),
            project_id=_uuid(run["project_id"]),
            run_id=_uuid(run["id"]),
            conversation_id=_uuid_or_none(run["conversation_id"]),
            report_title=str(run["report_title"] or "ResearchLens report"),
            sections=sections,
            chunks=chunks,
            sources=sources,
            citations=(),
            latest_evaluation_pass_id=await self._latest_pass(run_id, "evaluation_passes"),
            latest_repair_pass_id=await self._latest_pass(run_id, "repair_passes"),
            warnings=(),
        )

    async def _sections(self, *, run_id: UUID) -> tuple[FinalSection, ...]:
        rows = await self._mappings(_SECTIONS_SQL, {"run_id": _db_uuid(run_id)})
        return tuple(_section(row) for row in rows)

    async def _chunks(self, *, run_id: UUID) -> tuple[ExportChunk, ...]:
        rows = await self._mappings(_CHUNKS_SQL, {"run_id": _db_uuid(run_id)})
        return tuple(
            ExportChunk(
                chunk_id=_uuid(row["chunk_id"]),
                source_id=_uuid(row["source_id"]),
                chunk_index=int(row["chunk_index"]),
                text=str(row["text"]),
            )
            for row in rows
        )

    async def _sources(self, *, run_id: UUID) -> tuple[ExportSource, ...]:
        rows = await self._mappings(_SOURCES_SQL, {"run_id": _db_uuid(run_id)})
        return tuple(
            ExportSource(
                source_id=_uuid(row["source_id"]),
                canonical_key=str(row["canonical_key"]),
                title=str(row["title"]) if row["title"] is not None else None,
                identifiers=_json_dict(row["identifiers_json"]),
                metadata=_json_dict(row["metadata_json"]),
            )
            for row in rows
        )

    async def _latest_pass(self, run_id: UUID, table_name: str) -> UUID | None:
        row = await self._mapping(
            f"select id from {table_name} where run_id = :run_id order by pass_index desc limit 1",
            {"run_id": _db_uuid(run_id)},
        )
        return _uuid_or_none(row["id"]) if row is not None else None

    async def _mapping(self, sql: str, params: dict[str, object]) -> dict[str, Any] | None:
        result = await self._session.execute(text(sql), params)
        row = result.mappings().first()
        return dict(row) if row is not None else None

    async def _mappings(self, sql: str, params: dict[str, object]) -> tuple[dict[str, Any], ...]:
        result = await self._session.execute(text(sql), params)
        return tuple(dict(row) for row in result.mappings().all())


def _section(row: dict[str, Any]) -> FinalSection:
    repaired = bool(row["repair_changed"]) and row["revised_text"] is not None
    return FinalSection(
        section_id=str(row["section_id"]),
        title=str(row["title"]),
        section_order=int(row["section_order"]),
        text=str(row["revised_text"] if repaired else row["section_text"]),
        summary=str(row["revised_summary"] if repaired else row["section_summary"]),
        repaired=repaired,
        draft_id=_uuid(row["draft_id"]),
        repair_result_id=_uuid_or_none(row["repair_result_id"]),
    )


def _uuid(value: object) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def _uuid_or_none(value: object) -> UUID | None:
    return None if value is None else _uuid(value)


def _db_uuid(value: UUID) -> str:
    return value.hex


def _json_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        parsed = json.loads(value)
        return dict(parsed) if isinstance(parsed, dict) else {}
    return {}


_RUN_SQL = """
select r.id, r.tenant_id, r.project_id, r.conversation_id, d.report_title
from runs r
left join (
    select run_id, title as report_title from drafting_report_drafts
) d on d.run_id = r.id
where r.id = :run_id
"""

_SECTIONS_SQL = """
select d.id as draft_id, d.section_id, d.section_order, d.title,
       d.section_text, d.section_summary,
       rr.id as repair_result_id, rr.changed as repair_changed,
       rr.revised_text, rr.revised_summary
from drafting_section_drafts d
left join repair_results rr on rr.id = (
    select latest.id from repair_results latest
    join repair_passes rp on rp.id = latest.repair_pass_id
    where latest.run_id = d.run_id
      and latest.section_id = d.section_id
      and latest.status = 'completed'
    order by rp.pass_index desc
    limit 1
)
where d.run_id = :run_id
order by d.section_order asc, d.section_id asc
"""

_CHUNKS_SQL = """
select distinct c.id as chunk_id, snap.source_id, c.chunk_index, c.text
from drafting_section_evidence e
join retrieval_source_chunks c on c.id = e.chunk_id
join retrieval_source_snapshots snap on snap.id = c.snapshot_id
where e.run_id = :run_id
order by snap.source_id asc, c.chunk_index asc
"""

_SOURCES_SQL = """
with source_ids as (
    select distinct snap.source_id
    from retrieval_source_snapshots snap
    join retrieval_source_chunks c on c.snapshot_id = snap.id
    join drafting_section_evidence e on e.chunk_id = c.id
    where e.run_id = :run_id
)
select s.id as source_id, s.canonical_key, s.title, s.identifiers_json, s.metadata_json
from retrieval_sources s
join source_ids on source_ids.source_id = s.id
order by s.title asc, s.canonical_key asc
"""
