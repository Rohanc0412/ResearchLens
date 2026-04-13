from uuid import UUID

from fastapi import APIRouter

from researchlens.modules.repair.application import (
    LatestRepairSummaryQuery,
)
from researchlens.modules.repair.presentation.dependencies import (
    LatestRepairSummaryDep,
    RequestActorDep,
)
from researchlens.modules.repair.presentation.repair_response_models import (
    RepairSectionResponse,
    RepairSummaryResponse,
)

router = APIRouter(tags=["repair"])


@router.get("/runs/{run_id}/repair", response_model=RepairSummaryResponse | None)
async def get_run_repair(
    run_id: UUID,
    actor: RequestActorDep,
    use_case: LatestRepairSummaryDep,
) -> RepairSummaryResponse | None:
    summary = await use_case.execute(
        LatestRepairSummaryQuery(tenant_id=actor.tenant_id, run_id=run_id)
    )
    return RepairSummaryResponse.model_validate(summary) if summary is not None else None


@router.get("/runs/{run_id}/repair/sections", response_model=tuple[RepairSectionResponse, ...])
async def list_run_repair_sections(
    run_id: UUID,
    actor: RequestActorDep,
    use_case: LatestRepairSummaryDep,
) -> tuple[RepairSectionResponse, ...]:
    summary = await use_case.execute(
        LatestRepairSummaryQuery(tenant_id=actor.tenant_id, run_id=run_id)
    )
    if summary is None:
        return ()
    return tuple(RepairSectionResponse.model_validate(item) for item in summary.sections)
