from datetime import datetime

from researchlens.modules.runs.domain import RunStage, RunStatus

DISPLAY_STATUS_LABELS = {
    RunStatus.CREATED: "Waiting",
    RunStatus.QUEUED: "Waiting",
    RunStatus.RUNNING: "Running",
    RunStatus.FAILED: "Failed",
    RunStatus.CANCELED: "Stopped",
    RunStatus.SUCCEEDED: "Completed",
}

DISPLAY_STAGE_LABELS = {
    None: "Preparing run",
    RunStage.RETRIEVE: "Searching for sources",
    RunStage.INGEST: "Ingesting source material",
    RunStage.OUTLINE: "Building outline",
    RunStage.EVIDENCE_PACK: "Preparing evidence pack",
    RunStage.DRAFT: "Drafting report",
    RunStage.EVALUATE: "Checking quality",
    RunStage.VALIDATE: "Validating findings",
    RunStage.REPAIR: "Repairing issues",
    RunStage.FACTCHECK: "Checking facts",
    RunStage.EXPORT: "Exporting result",
}


def display_status_for(status: RunStatus) -> str:
    return DISPLAY_STATUS_LABELS[status]


def display_stage_for(
    *,
    stage: RunStage | None,
    status: RunStatus,
    cancel_requested: bool,
    started_at: datetime | None,
) -> str:
    if status == RunStatus.CANCELED and started_at is None:
        return "Preparing run"
    if cancel_requested and status == RunStatus.RUNNING:
        return DISPLAY_STAGE_LABELS.get(stage, "Preparing run")
    return DISPLAY_STAGE_LABELS.get(stage, "Preparing run")
