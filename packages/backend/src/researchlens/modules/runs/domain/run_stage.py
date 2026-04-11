from enum import StrEnum

from researchlens.shared.errors import ValidationError


class RunStage(StrEnum):
    RETRIEVE = "retrieve"
    INGEST = "ingest"
    OUTLINE = "outline"
    EVIDENCE_PACK = "evidence_pack"
    DRAFT = "draft"
    EVALUATE = "evaluate"
    VALIDATE = "validate"
    REPAIR = "repair"
    FACTCHECK = "factcheck"
    EXPORT = "export"


RUN_STAGE_SEQUENCE = (
    RunStage.RETRIEVE,
    RunStage.DRAFT,
    RunStage.EVALUATE,
    RunStage.EXPORT,
)


def normalize_run_stage(value: str | RunStage | None) -> RunStage | None:
    if value is None or isinstance(value, RunStage):
        return value
    try:
        return RunStage(value)
    except ValueError as exc:
        raise ValidationError(f"Unknown run stage: {value}.") from exc
