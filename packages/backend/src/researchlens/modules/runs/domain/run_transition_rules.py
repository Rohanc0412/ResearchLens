from researchlens.modules.runs.domain.run_status import RunStatus
from researchlens.shared.errors import ConflictError

ALLOWED_RUN_STATUS_TRANSITIONS = {
    RunStatus.CREATED: {RunStatus.QUEUED, RunStatus.CANCELED},
    RunStatus.QUEUED: {RunStatus.RUNNING, RunStatus.CANCELED},
    RunStatus.RUNNING: {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELED},
    RunStatus.FAILED: {RunStatus.QUEUED},
    RunStatus.CANCELED: set(),
    RunStatus.SUCCEEDED: set(),
}


def ensure_run_transition_allowed(*, current: RunStatus, target: RunStatus) -> None:
    if current == target:
        return
    allowed_targets = ALLOWED_RUN_STATUS_TRANSITIONS[current]
    if target in allowed_targets:
        return
    raise ConflictError(f"Run status transition {current.value} -> {target.value} is not allowed.")
