import re
from typing import Any
from uuid import UUID

from pydantic import ValidationError as PydanticValidationError

from researchlens.modules.repair.application.dtos import RepairOutputPayload, SectionRepairInput
from researchlens.shared.errors import ValidationError

TOKEN_PATTERN = re.compile(
    r"\[\[chunk:(?P<chunk_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\]\]"
)


def parse_repair_output(
    *,
    data: dict[str, Any],
    repair_input: SectionRepairInput,
) -> RepairOutputPayload:
    try:
        payload = RepairOutputPayload.model_validate(data)
    except PydanticValidationError as exc:
        raise ValidationError("Repair model output did not match the required schema.") from exc
    validate_repair_output(payload=payload, repair_input=repair_input)
    return payload


def validate_repair_output(
    *,
    payload: RepairOutputPayload,
    repair_input: SectionRepairInput,
) -> None:
    if payload.section_id != repair_input.section_id:
        raise ValidationError("Repair model output section id did not match the requested section.")
    known_issue_ids = {issue.issue_id for issue in repair_input.issues}
    if any(issue_id not in known_issue_ids for issue_id in payload.addressed_issue_ids):
        raise ValidationError("Repair model output addressed an unknown issue id.")
    citation_tokens = _parse_citation_tokens(payload.revised_text)
    allowed = set(repair_input.allowed_chunk_ids)
    if not citation_tokens:
        raise ValidationError("Repair model output must include at least one citation.")
    if any(chunk_id not in allowed for chunk_id in citation_tokens):
        raise ValidationError("Repair model output cited evidence outside the allowed pack.")
    if any(chunk_id not in allowed for chunk_id in payload.citations_used):
        raise ValidationError("Repair model output reported a disallowed citation.")


def invalid_citation_ids(*, cited: tuple[UUID, ...], allowed: tuple[UUID, ...]) -> tuple[UUID, ...]:
    allowed_set = set(allowed)
    return tuple(chunk_id for chunk_id in cited if chunk_id not in allowed_set)


def _parse_citation_tokens(text: str) -> tuple[UUID, ...]:
    return tuple(UUID(match.group("chunk_id")) for match in TOKEN_PATTERN.finditer(text))
