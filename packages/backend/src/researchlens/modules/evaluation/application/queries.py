from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.evaluation.application.dtos import (
    EvaluationIssuePayload,
    EvaluationSummary,
    RepairCandidatePayload,
)
from researchlens.modules.evaluation.application.ports import EvaluationRepository


@dataclass(frozen=True, slots=True)
class LatestEvaluationSummaryQuery:
    tenant_id: UUID
    run_id: UUID


class GetLatestEvaluationSummaryUseCase:
    def __init__(self, repository: EvaluationRepository) -> None:
        self._repository = repository

    async def execute(self, query: LatestEvaluationSummaryQuery) -> EvaluationSummary | None:
        return await self._repository.latest_summary(
            tenant_id=query.tenant_id,
            run_id=query.run_id,
        )


@dataclass(frozen=True, slots=True)
class ListEvaluationIssuesQuery:
    tenant_id: UUID
    run_id: UUID
    section_id: str | None = None


class ListEvaluationIssuesUseCase:
    def __init__(self, repository: EvaluationRepository) -> None:
        self._repository = repository

    async def execute(self, query: ListEvaluationIssuesQuery) -> tuple[EvaluationIssuePayload, ...]:
        return await self._repository.list_issues(
            tenant_id=query.tenant_id,
            run_id=query.run_id,
            section_id=query.section_id,
        )


@dataclass(frozen=True, slots=True)
class LoadRepairCandidatesQuery:
    tenant_id: UUID
    run_id: UUID


class LoadRepairCandidatesUseCase:
    def __init__(self, repository: EvaluationRepository) -> None:
        self._repository = repository

    async def execute(self, query: LoadRepairCandidatesQuery) -> tuple[RepairCandidatePayload, ...]:
        return await self._repository.load_repair_candidates(
            tenant_id=query.tenant_id,
            run_id=query.run_id,
        )
