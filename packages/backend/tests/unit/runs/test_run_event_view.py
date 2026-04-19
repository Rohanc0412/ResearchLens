from datetime import UTC, datetime
from uuid import uuid4

from researchlens.modules.runs.application.dto import to_run_event_view
from researchlens.modules.runs.domain import (
    RunEventAudience,
    RunEventLevel,
    RunEventRecord,
    RunEventType,
    RunStage,
    RunStatus,
)


def test_to_run_event_view_exposes_audience_and_level() -> None:
    event = RunEventRecord(
        id=uuid4(),
        run_id=uuid4(),
        event_number=7,
        event_type=RunEventType.CHECKPOINT_WRITTEN,
        audience=RunEventAudience.PROGRESS,
        level=RunEventLevel.WARN,
        status=RunStatus.RUNNING,
        stage=RunStage.DRAFT,
        message="Draft section correction retry",
        payload_json={"section_id": "summary"},
        retry_count=0,
        cancel_requested=False,
        created_at=datetime.now(tz=UTC),
        event_key="attempt-0:draft.correction_retry:summary:1",
    )

    view = to_run_event_view(event)

    assert view.audience == "progress"
    assert view.level == "warn"
    assert view.stage == "draft"
