from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, cast
from uuid import UUID

from researchlens.modules.repair.application.dtos import (
    RepairEvidenceRef,
    RepairIssueInput,
    RepairPassRecord,
    RepairReadSection,
    SectionRepairInput,
)
from researchlens.modules.repair.infrastructure.rows import RepairResultRow


def issue_input(row: Mapping[str, Any]) -> RepairIssueInput:
    return RepairIssueInput(
        issue_id=cast(UUID, row["id"]),
        issue_type=cast(str, row["issue_type"]),
        severity=cast(str, row["severity"]),
        verdict=cast(str | None, row["verdict"]),
        rationale=cast(str, row["rationale"]),
        message=cast(str, row["message"]),
        claim_id=cast(UUID | None, row["claim_id"]),
        claim_index=cast(int | None, row["claim_index"]),
        claim_text=cast(str | None, row["claim_text"]),
        cited_chunk_ids=tuple(UUID(item) for item in row["cited_chunk_ids_json"]),
        supported_chunk_ids=tuple(UUID(item) for item in row["supported_chunk_ids_json"]),
        allowed_chunk_ids=tuple(UUID(item) for item in row["allowed_chunk_ids_json"]),
        repair_hint=cast(str, row["repair_hint"]),
    )


def evidence_ref(row: Mapping[str, Any]) -> RepairEvidenceRef:
    return RepairEvidenceRef(
        chunk_id=cast(UUID, row["chunk_id"]),
        source_id=cast(UUID, row["source_id"]),
        source_title=cast(str, row["source_title"]),
        source_rank=cast(int, row["source_rank"]),
        chunk_index=cast(int, row["chunk_index"]),
        text=cast(str, row["excerpt_text"]),
    )


def result_row(
    result_id: UUID,
    repair_pass: RepairPassRecord,
    repair_input: SectionRepairInput,
    status: str,
    action: str,
    now: datetime,
) -> RepairResultRow:
    return RepairResultRow(
        id=result_id,
        tenant_id=repair_input.tenant_id,
        repair_pass_id=repair_pass.id,
        run_id=repair_input.run_id,
        evaluation_section_result_id=repair_input.evaluation_section_result_id,
        evaluation_pass_id=repair_input.evaluation_pass_id,
        section_id=repair_input.section_id,
        section_title=repair_input.section_title,
        section_order=repair_input.section_order,
        status=status,
        action=action,
        changed=False,
        issue_ids_json=[str(issue.issue_id) for issue in repair_input.issues],
        original_text=None,
        original_summary=None,
        revised_text=None,
        revised_summary=None,
        validation_summary_json={},
        unresolved_reason=None,
        reevaluation_pass_id=None,
        started_at=now,
        completed_at=None,
        created_at=now,
        updated_at=now,
    )


def assemble_markdown(*, title: str, rows: Sequence[Mapping[str, Any]]) -> str:
    parts = [f"# {title}"]
    for row in rows:
        parts.append(f"## {row['section_order']}. {row['title']}")
        parts.append(str(row["section_text"]))
    return "\n\n".join(parts)


def read_section(row: RepairResultRow) -> RepairReadSection:
    return RepairReadSection(
        section_id=row.section_id,
        section_title=row.section_title,
        section_order=row.section_order,
        status=row.status,
        action=row.action,
        changed=row.changed,
        evaluation_section_result_id=row.evaluation_section_result_id,
        repair_result_id=row.id,
        reevaluation_pass_id=row.reevaluation_pass_id,
        unresolved_reason=row.unresolved_reason,
    )
