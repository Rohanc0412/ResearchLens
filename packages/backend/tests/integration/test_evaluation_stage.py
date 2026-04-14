from uuid import UUID

import pytest
from sqlalchemy import func, select

from researchlens.modules.drafting.infrastructure import (
    SqlAlchemyDraftingRepository,
    SqlAlchemyDraftingRunInputReader,
)
from researchlens.modules.drafting.orchestration import (
    DraftingGraphRuntime,
    build_drafting_subgraph,
)
from researchlens.modules.evaluation.application.dtos import (
    EvaluatedClaimPayload,
    EvaluationRunInput,
    EvaluationSectionInput,
    SectionEvaluationResult,
)
from researchlens.modules.evaluation.domain import ClaimVerdict
from researchlens.modules.evaluation.infrastructure import (
    SqlAlchemyEvaluationInputReader,
    SqlAlchemyEvaluationRepository,
)
from researchlens.modules.evaluation.infrastructure.rows import (
    EvaluationClaimRow,
    EvaluationIssueRow,
    EvaluationPassRow,
    EvaluationSectionResultRow,
)
from researchlens.modules.evaluation.orchestration import (
    EvaluationGraphRuntime,
    build_evaluation_subgraph,
)
from researchlens.modules.evaluation.orchestration.progress import (
    EvaluationGraphCheckpointSink,
    EvaluationGraphEventSink,
)
from researchlens.shared.config import get_settings, reset_settings_cache
from researchlens.shared.db import DatabaseRuntime

from .drafting_support import FakeDraftingClient, seed_run_with_retrieval_outputs


class _NoopEventWriter(EvaluationGraphEventSink):
    async def info(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        return None

    async def warning(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        return None


class _NoopCheckpointWriter(EvaluationGraphCheckpointSink):
    async def checkpoint(
        self,
        *,
        key: str,
        summary: dict[str, object],
        completed_stages: tuple[str, ...],
        next_stage: str | None,
    ) -> None:
        return None


class _SessionCancellationProbe:
    async def cancel_requested(self, *, run_id: UUID) -> bool:
        return False


class _FakeEvaluationEvaluator:
    async def evaluate_section(
        self,
        *,
        evaluation_pass_id: UUID,
        run_input: EvaluationRunInput,
        section: EvaluationSectionInput,
    ) -> SectionEvaluationResult:
        verdict = (
            ClaimVerdict.CONTRADICTED
            if section.section_id == "risks"
            else ClaimVerdict.SUPPORTED
        )
        faithfulness = 95.0 if section.section_id == "risks" else 82.0
        return SectionEvaluationResult(
            section_id=section.section_id,
            section_title=section.section_title,
            section_order=section.section_order,
            claims=(
                EvaluatedClaimPayload(
                    claim_index=1,
                    claim_text=f"{section.section_id} claim",
                    verdict=verdict,
                    cited_chunk_ids=(section.allowed_chunk_ids[0],),
                    supported_chunk_ids=_supported_chunks(
                        verdict=verdict,
                        section=section,
                    ),
                    rationale="Evaluator rationale",
                    repair_hint="Review the cited evidence.",
                ),
            ),
            issues=(),
            quality_score=0.0,
            unsupported_claim_rate=0.0,
            ragas_faithfulness_pct=faithfulness,
            section_has_contradicted_claim=False,
            repair_recommended=False,
        )


@pytest.mark.asyncio
async def test_evaluation_subgraph_persists_queryable_repair_ready_outputs(
    database_runtime: DatabaseRuntime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    reset_settings_cache()
    async with database_runtime.session_factory() as session:
        tenant_id, run_id = await seed_run_with_retrieval_outputs(
            session,
            section_ids=("overview", "risks"),
        )
    await _draft_run(database_runtime, run_id=run_id)

    async with database_runtime.session_factory() as session:
        runtime = EvaluationGraphRuntime(
            settings=get_settings(),
            input_reader=SqlAlchemyEvaluationInputReader(session),
            repository=SqlAlchemyEvaluationRepository(session),
            evaluator=_FakeEvaluationEvaluator(),
            cancellation_probe=_SessionCancellationProbe(),
            events=_NoopEventWriter(),
            checkpoints=_NoopCheckpointWriter(),
        )
        state = await build_evaluation_subgraph(runtime).ainvoke(
            {"run_id": run_id, "completed_stages": ("retrieve", "draft")}
        )
        await session.commit()

    async with database_runtime.session_factory() as session:
        repository = SqlAlchemyEvaluationRepository(session)
        pass_count = await session.scalar(select(func.count()).select_from(EvaluationPassRow))
        section_count = await session.scalar(
            select(func.count()).select_from(EvaluationSectionResultRow)
        )
        claim_count = await session.scalar(select(func.count()).select_from(EvaluationClaimRow))
        issue_count = await session.scalar(select(func.count()).select_from(EvaluationIssueRow))
        summary = await repository.latest_summary(tenant_id=tenant_id, run_id=run_id)
        issues = await repository.list_issues(
            tenant_id=tenant_id,
            run_id=run_id,
            section_id="risks",
        )
        candidates = await repository.load_repair_candidates(tenant_id=tenant_id, run_id=run_id)

    assert pass_count == 1
    assert section_count == 2
    assert claim_count == 2
    assert issue_count == 1
    assert summary is not None
    assert summary.repair_recommended is True
    assert summary.sections_requiring_repair == ("risks",)
    assert state["repair_recommended"] is True
    assert issues[0].verdict == ClaimVerdict.CONTRADICTED
    assert [candidate.section_id for candidate in candidates if candidate.repair_recommended] == [
        "risks"
    ]




async def _draft_run(database_runtime: DatabaseRuntime, *, run_id: UUID) -> None:
    async with database_runtime.session_factory() as session:
        runtime = DraftingGraphRuntime(
            settings=get_settings(),
            input_reader=SqlAlchemyDraftingRunInputReader(session),
            repository=SqlAlchemyDraftingRepository(session),
            cancellation_probe=_SessionCancellationProbe(),
            events=_NoopEventWriter(),
            checkpoints=_NoopCheckpointWriter(),
            generation_client=FakeDraftingClient(),
        )
        await build_drafting_subgraph(runtime).ainvoke(
            {"run_id": run_id, "completed_stages": ("retrieve",)}
        )
        await session.commit()


def _supported_chunks(
    *,
    verdict: ClaimVerdict,
    section: EvaluationSectionInput,
) -> tuple[UUID, ...]:
    if verdict == ClaimVerdict.CONTRADICTED:
        return ()
    return (section.allowed_chunk_ids[0],)
