from enum import StrEnum


class RunStatus(StrEnum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


TERMINAL_RUN_STATUSES = {
    RunStatus.SUCCEEDED,
    RunStatus.FAILED,
    RunStatus.CANCELED,
}

STOPPABLE_RUN_STATUSES = {
    RunStatus.QUEUED,
    RunStatus.RUNNING,
}
