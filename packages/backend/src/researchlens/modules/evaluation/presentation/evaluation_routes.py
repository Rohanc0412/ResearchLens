from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from researchlens.modules.evaluation.application import (
    GetLatestEvaluationSummaryUseCase,
    LatestEvaluationSummaryQuery,
    ListEvaluationIssuesQuery,
    ListEvaluationIssuesUseCase,
)
from researchlens.modules.evaluation.presentation.dependencies import (
    RequestActorDep,
    get_latest_summary_use_case,
    get_list_issues_use_case,
)
from researchlens.modules.evaluation.presentation.evaluation_response_models import (
    EvaluationIssueResponse,
    EvaluationSummaryResponse,
)
from researchlens.shared.errors import NotFoundError

router = APIRouter(tags=["evaluation"])

SummaryUseCaseDep = Annotated[
    GetLatestEvaluationSummaryUseCase,
    Depends(get_latest_summary_use_case),
]
IssuesUseCaseDep = Annotated[ListEvaluationIssuesUseCase, Depends(get_list_issues_use_case)]


@router.get("/runs/{run_id}/evaluation", response_model=EvaluationSummaryResponse)
async def get_run_evaluation(
    run_id: UUID,
    actor: RequestActorDep,
    use_case: SummaryUseCaseDep,
) -> EvaluationSummaryResponse:
    summary = await use_case.execute(
        LatestEvaluationSummaryQuery(tenant_id=actor.tenant_id, run_id=run_id)
    )
    if summary is None:
        raise NotFoundError("Evaluation summary was not found.")
    return EvaluationSummaryResponse.model_validate(summary)


@router.get("/runs/{run_id}/evaluation/issues", response_model=list[EvaluationIssueResponse])
async def list_run_evaluation_issues(
    run_id: UUID,
    actor: RequestActorDep,
    use_case: IssuesUseCaseDep,
    section_id: str | None = Query(default=None),
) -> list[EvaluationIssueResponse]:
    issues = await use_case.execute(
        ListEvaluationIssuesQuery(
            tenant_id=actor.tenant_id,
            run_id=run_id,
            section_id=section_id,
        )
    )
    return [EvaluationIssueResponse.model_validate(issue) for issue in issues]
