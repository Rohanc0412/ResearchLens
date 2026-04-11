from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError as PydanticValidationError

from researchlens.modules.runs.application.retry_resume_policy import decide_retry_resume
from researchlens.modules.runs.domain import (
    Run,
    RunCheckpointRecord,
    RunStage,
    RunStatus,
    ensure_run_transition_allowed,
    normalize_run_stage,
)
from researchlens.modules.runs.presentation.run_request_models import CreateRunRequest
from researchlens.modules.runs.presentation.run_response_models import RunSummaryResponse
from researchlens.shared.errors import ConflictError, ValidationError


def test_run_transition_rules_allow_legal_transition() -> None:
    ensure_run_transition_allowed(current=RunStatus.CREATED, target=RunStatus.QUEUED)


def test_run_transition_rules_reject_illegal_transition() -> None:
    with pytest.raises(ConflictError):
        ensure_run_transition_allowed(current=RunStatus.QUEUED, target=RunStatus.SUCCEEDED)


def test_retry_resume_policy_uses_checkpoint_before_draft() -> None:
    now = datetime.now(tz=UTC)
    run = Run.create(
        id=uuid4(),
        tenant_id=uuid4(),
        project_id=uuid4(),
        conversation_id=uuid4(),
        created_by_user_id=uuid4(),
        output_type="report",
        trigger_message_id=None,
        client_request_id=None,
        created_at=now,
        updated_at=now,
    ).replace_values(status=RunStatus.FAILED, current_stage=RunStage.DRAFT, updated_at=now)
    checkpoint = RunCheckpointRecord(
        id=uuid4(),
        run_id=run.id,
        stage=RunStage.RETRIEVE,
        checkpoint_key="attempt-0:retrieve:completed",
        payload_json={"next_stage": "draft"},
        summary_json=None,
        created_at=now,
    )

    decision = decide_retry_resume(run=run, latest_checkpoint=checkpoint)

    assert decision.resume_from_stage == RunStage.RETRIEVE


def test_retry_resume_policy_uses_draft_after_draft_checkpoint() -> None:
    now = datetime.now(tz=UTC)
    run = Run.create(
        id=uuid4(),
        tenant_id=uuid4(),
        project_id=uuid4(),
        conversation_id=uuid4(),
        created_by_user_id=uuid4(),
        output_type="report",
        trigger_message_id=None,
        client_request_id=None,
        created_at=now,
        updated_at=now,
    ).replace_values(status=RunStatus.FAILED, current_stage=RunStage.EVALUATE, updated_at=now)
    checkpoint = RunCheckpointRecord(
        id=uuid4(),
        run_id=run.id,
        stage=RunStage.DRAFT,
        checkpoint_key="attempt-0:draft:completed",
        payload_json={"next_stage": "evaluate"},
        summary_json=None,
        created_at=now,
    )

    decision = decide_retry_resume(run=run, latest_checkpoint=checkpoint)

    assert decision.resume_from_stage == RunStage.DRAFT


def test_normalize_run_stage_rejects_unknown_value() -> None:
    with pytest.raises(ValidationError):
        normalize_run_stage("unknown")


def test_run_request_model_forbids_extra_fields() -> None:
    with pytest.raises(PydanticValidationError):
        CreateRunRequest.model_validate({"request_text": "go", "unexpected": True})


def test_run_response_model_forbids_extra_fields() -> None:
    with pytest.raises(PydanticValidationError):
        RunSummaryResponse.model_validate(
            {
                "id": str(uuid4()),
                "project_id": str(uuid4()),
                "conversation_id": str(uuid4()),
                "status": "queued",
                "current_stage": "retrieve",
                "output_type": "report",
                "client_request_id": None,
                "retry_count": 0,
                "cancel_requested": False,
                "created_at": datetime.now(tz=UTC).isoformat(),
                "updated_at": datetime.now(tz=UTC).isoformat(),
                "started_at": None,
                "finished_at": None,
                "failure_reason": None,
                "error_code": None,
                "last_event_number": 0,
                "display_status": "Waiting",
                "display_stage": "Searching for sources",
                "can_stop": True,
                "can_retry": False,
                "unexpected": True,
            }
        )
