import json
from collections import defaultdict
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.evidence.application.dtos import (
    ChunkDetail,
    EvidenceChunkRef,
    EvidenceClaimTrace,
    EvidenceIssueTrace,
    EvidenceSectionSummary,
    EvidenceSourceRef,
    RunEvidenceSummary,
    SectionEvidenceTrace,
    SourceDetail,
)
from researchlens.modules.evidence.infrastructure import evidence_sql_statements as sql


class SqlAlchemyEvidenceQueries:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def run_summary(self, *, tenant_id: UUID, run_id: UUID) -> RunEvidenceSummary | None:
        row = await self._one(
            sql.RUN_SUMMARY_SQL,
            {"tenant_id": _db_uuid(tenant_id), "run_id": _db_uuid(run_id)},
        )
        if row is None:
            return None
        sections = await self._all(sql.SECTION_SUMMARIES_SQL, {"run_id": _db_uuid(run_id)})
        return RunEvidenceSummary(
            run_id=_uuid(row["run_id"]),
            project_id=_uuid(row["project_id"]),
            conversation_id=_uuid_or_none(row["conversation_id"]),
            section_count=int(row["section_count"] or 0),
            source_count=int(row["source_count"] or 0),
            chunk_count=int(row["chunk_count"] or 0),
            claim_count=int(row["claim_count"] or 0),
            issue_count=int(row["issue_count"] or 0),
            repaired_section_count=int(row["repaired_section_count"] or 0),
            unresolved_section_count=int(row["unresolved_section_count"] or 0),
            latest_evaluation_pass_id=_uuid_or_none(row["latest_evaluation_pass_id"]),
            latest_repair_pass_id=_uuid_or_none(row["latest_repair_pass_id"]),
            artifact_count=int(row["artifact_count"] or 0),
            sections=tuple(_section_summary(item) for item in sections),
        )

    async def section_trace(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
        section_id: str,
    ) -> SectionEvidenceTrace | None:
        params: dict[str, object] = {
            "tenant_id": _db_uuid(tenant_id),
            "run_id": _db_uuid(run_id),
            "section_id": section_id,
        }
        row = await self._one(sql.SECTION_TRACE_SQL, params)
        if row is None:
            return None
        issues = tuple(_issue(item) for item in await self._all(sql.SECTION_ISSUES_SQL, params))
        claims = await self._claims(params)
        chunks = tuple(
            _chunk_ref(item) for item in await self._all(sql.SECTION_CHUNKS_SQL, params)
        )
        sources = tuple(
            _source_ref(item) for item in await self._all(sql.SECTION_SOURCES_SQL, params)
        )
        return SectionEvidenceTrace(
            section_id=str(row["section_id"]),
            section_title=str(row["title"]),
            section_order=int(row["section_order"]),
            canonical_text=str(row["canonical_text"]),
            canonical_summary=str(row["canonical_summary"]),
            repaired=bool(row["repaired"]),
            latest_evaluation_result_id=_uuid_or_none(row["evaluation_result_id"]),
            repair_result_id=_uuid_or_none(row["repair_result_id"]),
            claims=claims,
            issues=issues,
            evidence_chunks=chunks,
            source_refs=sources,
            unresolved_quality_findings=issues,
        )

    async def chunk_detail(
        self,
        *,
        tenant_id: UUID,
        chunk_id: UUID,
        context_window: int,
    ) -> ChunkDetail | None:
        row = await self._one(
            sql.CHUNK_DETAIL_SQL,
            {"tenant_id": _db_uuid(tenant_id), "chunk_id": _db_uuid(chunk_id)},
        )
        if row is None:
            return None
        context = await self._all(
            sql.CHUNK_CONTEXT_SQL,
            {
                "snapshot_id": str(row["snapshot_id"]),
                "start": int(row["chunk_index"]) - context_window,
                "end": int(row["chunk_index"]) + context_window,
            },
        )
        usage = await self._all(
            sql.CHUNK_USAGE_SQL,
            {"tenant_id": _db_uuid(tenant_id), "chunk_id": _db_uuid(chunk_id)},
        )
        return ChunkDetail(
            chunk_id=_uuid(row["chunk_id"]),
            source_id=_uuid(row["source_id"]),
            source_title=_str_or_none(row["title"]),
            source_url=_metadata_url(row["metadata_json"]),
            identifiers=_json_dict(row["identifiers_json"]),
            chunk_text=str(row["text"]),
            chunk_index=int(row["chunk_index"]),
            context_chunks=tuple(_chunk_ref(item) for item in context),
            run_ids=tuple(_uuid(item["run_id"]) for item in usage),
            section_ids=tuple(str(item["section_id"]) for item in usage),
        )

    async def source_detail(self, *, tenant_id: UUID, source_id: UUID) -> SourceDetail | None:
        row = await self._one(
            sql.SOURCE_DETAIL_SQL,
            {"tenant_id": _db_uuid(tenant_id), "source_id": _db_uuid(source_id)},
        )
        if row is None:
            return None
        metadata = _json_dict(row["metadata_json"])
        return SourceDetail(
            source_id=_uuid(row["source_id"]),
            canonical_key=str(row["canonical_key"]),
            title=_str_or_none(row["title"]),
            authors=_authors(metadata.get("authors")),
            venue=_str_or_none(metadata.get("venue")),
            year=_int_or_none(metadata.get("year")),
            url=_metadata_url(row["metadata_json"]),
            provider_metadata=metadata,
            identifiers=_json_dict(row["identifiers_json"]),
            run_usage_count=int(row["run_usage_count"] or 0),
        )

    async def _claims(self, params: dict[str, object]) -> tuple[EvidenceClaimTrace, ...]:
        claim_rows = await self._all(sql.SECTION_CLAIMS_SQL, params)
        issue_rows = await self._all(sql.SECTION_ISSUES_SQL, params)
        issues_by_claim: dict[UUID, list[dict[str, Any]]] = defaultdict(list)
        for issue in issue_rows:
            if issue["claim_id"] is not None:
                issues_by_claim[_uuid(issue["claim_id"])].append(issue)
        return tuple(_claim(row, issues_by_claim[_uuid(row["claim_id"])]) for row in claim_rows)

    async def _one(self, sql: str, params: dict[str, object]) -> dict[str, Any] | None:
        result = await self._session.execute(text(sql), params)
        row = result.mappings().first()
        return dict(row) if row is not None else None

    async def _all(self, sql: str, params: dict[str, object]) -> tuple[dict[str, Any], ...]:
        result = await self._session.execute(text(sql), params)
        return tuple(dict(row) for row in result.mappings().all())


def _section_summary(row: dict[str, Any]) -> EvidenceSectionSummary:
    return EvidenceSectionSummary(
        section_id=str(row["section_id"]),
        title=str(row["title"]),
        section_order=int(row["section_order"]),
        repaired=bool(row["repaired"]),
        issue_count=int(row["issue_count"] or 0),
    )


def _claim(row: dict[str, Any], issues: list[dict[str, Any]]) -> EvidenceClaimTrace:
    return EvidenceClaimTrace(
        claim_id=_uuid(row["claim_id"]),
        claim_index=int(row["claim_index"]),
        claim_text=str(row["claim_text"]),
        verdict=_str_or_none(row["verdict"]),
        cited_chunk_ids=_uuid_tuple(_first_json_list(issues, "cited_chunk_ids_json")),
        supported_chunk_ids=_uuid_tuple(_first_json_list(issues, "supported_chunk_ids_json")),
        allowed_chunk_ids=_uuid_tuple(_first_json_list(issues, "allowed_chunk_ids_json")),
        issue_ids=tuple(_uuid(item["issue_id"]) for item in issues),
    )


def _issue(row: dict[str, Any]) -> EvidenceIssueTrace:
    return EvidenceIssueTrace(
        issue_id=_uuid(row["issue_id"]),
        issue_type=str(row["issue_type"]),
        severity=str(row["severity"]),
        verdict=_str_or_none(row["verdict"]),
        message=str(row["message"]),
        rationale=str(row["rationale"]),
        repair_hint=str(row["repair_hint"]),
    )


def _chunk_ref(row: dict[str, Any]) -> EvidenceChunkRef:
    return EvidenceChunkRef(
        chunk_id=_uuid(row["chunk_id"]),
        source_id=_uuid(row["source_id"]),
        source_title=_str_or_none(row["source_title"]),
        chunk_index=int(row["chunk_index"]),
        excerpt_text=str(row["excerpt_text"]),
    )


def _source_ref(row: dict[str, Any]) -> EvidenceSourceRef:
    return EvidenceSourceRef(
        source_id=_uuid(row["source_id"]),
        canonical_key=str(row["canonical_key"]),
        title=_str_or_none(row["title"]),
        identifiers=_json_dict(row["identifiers_json"]),
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


def _json_list(value: object) -> list[object]:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, str):
        parsed = json.loads(value)
        return list(parsed) if isinstance(parsed, list) else []
    return []


def _uuid_tuple(values: list[object]) -> tuple[UUID, ...]:
    return tuple(_uuid(item) for item in values)


def _first_json_list(rows: list[dict[str, Any]], key: str) -> list[object]:
    return _json_list(rows[0][key]) if rows else []


def _str_or_none(value: object) -> str | None:
    return str(value) if value is not None else None


def _int_or_none(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _authors(value: object) -> tuple[str, ...]:
    if isinstance(value, list | tuple):
        return tuple(str(item) for item in value if item)
    return ()


def _metadata_url(value: object) -> str | None:
    metadata = _json_dict(value)
    url = metadata.get("url") or metadata.get("source_url")
    return str(url) if url is not None else None
