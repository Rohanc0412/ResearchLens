from researchlens.modules.runs.application.dto import RetryDecision
from researchlens.modules.runs.domain import Run, RunCheckpointRecord, RunStage


def decide_retry_resume(
    *,
    run: Run,
    latest_checkpoint: RunCheckpointRecord | None,
) -> RetryDecision:
    if run.current_stage in {RunStage.EVALUATE, RunStage.REPAIR, RunStage.EXPORT}:
        return RetryDecision(
            resume_from_stage=RunStage.DRAFT,
            message="Retrying from drafting",
            payload={"resume_from_stage": RunStage.DRAFT.value},
        )
    if run.current_stage == RunStage.DRAFT and latest_checkpoint is not None:
        if latest_checkpoint.stage == RunStage.DRAFT:
            return RetryDecision(
                resume_from_stage=RunStage.DRAFT,
                message="Retrying from drafting",
                payload={"resume_from_stage": RunStage.DRAFT.value},
            )
    if run.current_stage == RunStage.DRAFT and latest_checkpoint is None:
        return RetryDecision(
            resume_from_stage=RunStage.DRAFT,
            message="Retrying from drafting",
            payload={"resume_from_stage": RunStage.DRAFT.value},
        )
    if latest_checkpoint is not None:
        return RetryDecision(
            resume_from_stage=latest_checkpoint.stage,
            message="Retrying from the last saved step",
            payload={"resume_from_checkpoint": latest_checkpoint.checkpoint_key},
        )
    return RetryDecision(
        resume_from_stage=RunStage.RETRIEVE,
        message="Retrying from the last saved step",
        payload={"resume_from_stage": RunStage.RETRIEVE.value},
    )
