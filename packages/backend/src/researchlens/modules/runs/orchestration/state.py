from typing import Any, NotRequired, TypedDict
from uuid import UUID

from researchlens.modules.runs.domain import (
    RUN_STAGE_SEQUENCE,
    Run,
    RunCheckpointRecord,
    RunStage,
    RunStatus,
)


class RunGraphState(TypedDict):
    run_id: UUID
    queue_item_id: UUID
    lease_token: UUID
    tenant_id: UUID
    conversation_id: UUID | None
    output_type: str
    retry_count: int
    request_text: str
    current_stage: str | None
    start_stage: str
    completed_stages: tuple[str, ...]
    latest_checkpoint_key: str | None
    latest_checkpoint_stage: str | None
    cancel_requested: bool
    resuming: bool
    loaded_run: NotRequired[Run]
    latest_checkpoint: NotRequired[RunCheckpointRecord | None]
    terminal_status: NotRequired[str]
    retrieval_planning: NotRequired[Any]
    retrieval_selection: NotRequired[Any]
    retrieval_summary: NotRequired[Any]
    drafting_prepared: NotRequired[Any]
    drafting_result: NotRequired[Any]
    evaluation_summary: NotRequired[Any]
    sections_requiring_repair: NotRequired[Any]
    repair_recommended: NotRequired[bool]
    evaluation_status: NotRequired[str]
    evaluation_failure_summary: NotRequired[Any]
    repair_summary: NotRequired[Any]
    repaired_section_ids: NotRequired[Any]
    repair_result_ids_by_section: NotRequired[Any]
    reevaluation_summary: NotRequired[Any]
    artifact_export_summary: NotRequired[Any]
    target_section_ids: NotRequired[tuple[str, ...]]
    evaluation_scope: NotRequired[str]


def initial_run_graph_state(
    *,
    run_id: UUID,
    queue_item_id: UUID,
    lease_token: UUID,
) -> RunGraphState:
    return {
        "run_id": run_id,
        "queue_item_id": queue_item_id,
        "lease_token": lease_token,
        "tenant_id": UUID(int=0),
        "conversation_id": None,
        "output_type": "",
        "retry_count": 0,
        "request_text": "",
        "current_stage": None,
        "start_stage": RunStage.RETRIEVE.value,
        "completed_stages": tuple(),
        "latest_checkpoint_key": None,
        "latest_checkpoint_stage": None,
        "cancel_requested": False,
        "resuming": False,
    }


def restore_graph_state(
    *,
    run: Run,
    request_text: str,
    latest_checkpoint: RunCheckpointRecord | None,
) -> RunGraphState:
    payload = latest_checkpoint.payload_json if latest_checkpoint is not None else None
    completed_stages = tuple(_completed_stages(payload))
    next_stage = _next_stage(payload, run.current_stage)
    if (
        run.status == RunStatus.QUEUED
        and run.current_stage is not None
        and run.current_stage != next_stage
    ):
        next_stage = run.current_stage
        completed_stages = _completed_before(next_stage)
    return {
        "run_id": run.id,
        "queue_item_id": UUID(int=0),
        "lease_token": UUID(int=0),
        "tenant_id": run.tenant_id,
        "conversation_id": run.conversation_id,
        "output_type": run.output_type,
        "retry_count": run.retry_count,
        "request_text": request_text,
        "current_stage": run.current_stage.value if run.current_stage is not None else None,
        "start_stage": next_stage.value,
        "completed_stages": completed_stages,
        "latest_checkpoint_key": latest_checkpoint.checkpoint_key if latest_checkpoint else None,
        "latest_checkpoint_stage": latest_checkpoint.stage.value if latest_checkpoint else None,
        "cancel_requested": run.cancel_requested_at is not None,
        "resuming": latest_checkpoint is not None,
    }


def checkpoint_stage_values(state: RunGraphState) -> tuple[RunStage, ...]:
    return tuple(RunStage(value) for value in state["completed_stages"])


def _completed_stages(payload: dict[str, object] | None) -> tuple[str, ...]:
    raw = payload.get("completed_stages") if payload else None
    if not isinstance(raw, list):
        return tuple()
    return tuple(str(item) for item in raw)


def _next_stage(
    payload: dict[str, object] | None,
    current_stage: RunStage | None,
) -> RunStage:
    if payload is not None:
        value = payload.get("next_stage")
        if isinstance(value, str) and value:
            return RunStage(value)
        if "completed_stages" in payload and current_stage is not None:
            return current_stage
    return current_stage or RunStage.RETRIEVE


def _completed_before(stage: RunStage) -> tuple[str, ...]:
    return tuple(item.value for item in RUN_STAGE_SEQUENCE[: RUN_STAGE_SEQUENCE.index(stage)])
