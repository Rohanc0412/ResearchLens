from collections.abc import Mapping
from typing import Any, cast
from uuid import UUID

from sqlalchemy import Select, Table, select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.repair.application.dtos import (
    RepairEvidenceRef,
    RepairIssueInput,
    SectionRepairInput,
)
from researchlens.modules.repair.infrastructure.repair_row_mapping import (
    evidence_ref,
    issue_input,
)
from researchlens.shared.db import metadata


class RepairInputLoader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load_inputs(self, *, run_id: UUID) -> tuple[SectionRepairInput, ...]:
        latest = await self._latest_pipeline_pass(run_id=run_id)
        if latest is None:
            return ()
        rows = (await self._session.execute(self._input_query(latest["id"]))).mappings().all()
        inputs: list[SectionRepairInput] = []
        for row in rows:
            inputs.append(await self._input_from_row(cast(Mapping[str, Any], row)))
        return tuple(inputs)

    def _input_query(self, evaluation_pass_id: object) -> Select[Any]:
        section = _table("evaluation_section_results")
        draft = _table("drafting_section_drafts")
        return (
            select(
                section.c.id.label("evaluation_section_result_id"),
                section.c.tenant_id,
                section.c.run_id,
                section.c.evaluation_pass_id,
                section.c.section_id,
                section.c.section_title,
                section.c.section_order,
                section.c.repair_attempt_count,
                section.c.ragas_faithfulness_pct,
                section.c.section_has_contradicted_claim,
                draft.c.section_text,
                draft.c.section_summary,
            )
            .join(
                draft,
                (draft.c.run_id == section.c.run_id)
                & (draft.c.section_id == section.c.section_id),
            )
            .where(section.c.evaluation_pass_id == evaluation_pass_id)
            .order_by(section.c.section_order.asc(), section.c.section_id.asc())
        )

    async def _input_from_row(self, row: Mapping[str, Any]) -> SectionRepairInput:
        return SectionRepairInput(
            tenant_id=cast(UUID, row["tenant_id"]),
            run_id=cast(UUID, row["run_id"]),
            section_id=cast(str, row["section_id"]),
            section_title=cast(str, row["section_title"]),
            section_order=cast(int, row["section_order"]),
            current_section_text=cast(str, row["section_text"]),
            current_section_summary=cast(str, row["section_summary"]),
            evaluation_section_result_id=cast(UUID, row["evaluation_section_result_id"]),
            evaluation_pass_id=cast(UUID, row["evaluation_pass_id"]),
            repair_attempt_count=cast(int, row["repair_attempt_count"]),
            ragas_faithfulness_pct=cast(float, row["ragas_faithfulness_pct"]),
            triggered_by_low_faithfulness=cast(float, row["ragas_faithfulness_pct"]) < 70.0,
            triggered_by_contradiction=cast(bool, row["section_has_contradicted_claim"]),
            issues=await self._issues(cast(UUID, row["evaluation_section_result_id"])),
            evidence=await self._evidence(cast(UUID, row["run_id"]), cast(str, row["section_id"])),
        )

    async def _issues(self, section_result_id: UUID) -> tuple[RepairIssueInput, ...]:
        issues = _table("evaluation_issues")
        rows = (
            await self._session.execute(
                select(issues)
                .where(issues.c.section_result_id == section_result_id)
                .order_by(issues.c.claim_index.asc(), issues.c.id.asc())
            )
        ).mappings().all()
        return tuple(issue_input(cast(dict[str, Any], row)) for row in rows)

    async def _evidence(self, run_id: UUID, section_id: str) -> tuple[RepairEvidenceRef, ...]:
        section = _table("drafting_sections")
        evidence = _table("drafting_section_evidence")
        rows = (
            await self._session.execute(
                select(evidence)
                .join(section, section.c.id == evidence.c.section_row_id)
                .where(section.c.run_id == run_id, section.c.section_id == section_id)
                .order_by(
                    evidence.c.source_rank.asc(),
                    evidence.c.chunk_index.asc(),
                    evidence.c.chunk_id.asc(),
                )
            )
        ).mappings().all()
        return tuple(evidence_ref(cast(dict[str, Any], row)) for row in rows)

    async def _latest_pipeline_pass(self, *, run_id: UUID) -> dict[str, object] | None:
        result = await self._session.execute(
            select(_table("evaluation_passes"))
            .where(
                _table("evaluation_passes").c.run_id == run_id,
                _table("evaluation_passes").c.scope == "pipeline",
                _table("evaluation_passes").c.status == "completed",
            )
            .order_by(_table("evaluation_passes").c.pass_index.desc())
            .limit(1)
        )
        return cast(dict[str, object] | None, result.mappings().first())


def _table(name: str) -> Table:
    return metadata.tables[name]
