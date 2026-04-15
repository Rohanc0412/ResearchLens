from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Protocol
from uuid import UUID

from researchlens.modules.evaluation.application.dtos import (
    EvaluationIssuePayload,
    EvaluationPassRecord,
    EvaluationRunInput,
    EvaluationSectionInput,
    EvaluationSummary,
    RepairCandidatePayload,
    SectionEvaluationResult,
)


class EvaluationInputReader(Protocol):
    async def load_run_evaluation_input(
        self,
        *,
        run_id: UUID,
        section_ids: tuple[str, ...] | None = None,
    ) -> EvaluationRunInput: ...


class EvaluationRepository(Protocol):
    async def create_pass(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
        scope: str,
    ) -> EvaluationPassRecord: ...

    async def persist_section_results(
        self,
        *,
        evaluation_pass: EvaluationPassRecord,
        section_results: tuple[SectionEvaluationResult, ...],
    ) -> None: ...

    async def finalize_pass(
        self,
        *,
        evaluation_pass: EvaluationPassRecord,
        summary: EvaluationSummary,
    ) -> None: ...

    async def latest_summary(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
    ) -> EvaluationSummary | None: ...

    async def list_issues(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
        section_id: str | None = None,
    ) -> tuple[EvaluationIssuePayload, ...]: ...

    async def load_repair_candidates(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
    ) -> tuple[RepairCandidatePayload, ...]: ...


class SectionGroundingEvaluator(Protocol):
    async def evaluate_section(
        self,
        *,
        evaluation_pass_id: UUID,
        run_input: EvaluationRunInput,
        section: EvaluationSectionInput,
    ) -> SectionEvaluationResult: ...


class RunCancellationProbe(Protocol):
    async def cancel_requested(self, *, run_id: UUID) -> bool: ...


class TransactionManager(Protocol):
    @asynccontextmanager
    async def boundary(self) -> AsyncIterator[None]:
        yield
