from researchlens.modules.runs.domain import RunStage


def stage_started_message(stage: RunStage) -> str:
    if stage == RunStage.RETRIEVE:
        return "Searching for relevant sources"
    if stage == RunStage.DRAFT:
        return "Drafting report"
    if stage == RunStage.EVALUATE:
        return "Checking quality"
    return "Exporting result"


def stage_completed_message(stage: RunStage) -> str:
    if stage == RunStage.RETRIEVE:
        return "Source search complete"
    if stage == RunStage.DRAFT:
        return "Drafting complete"
    if stage == RunStage.EVALUATE:
        return "Quality check complete"
    return "Export complete"
