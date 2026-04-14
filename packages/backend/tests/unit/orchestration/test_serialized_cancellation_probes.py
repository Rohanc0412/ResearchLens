import asyncio
from uuid import uuid4

import pytest

from researchlens.modules.drafting.application.drafting_stage_steps import DraftingStageSteps
from researchlens.modules.evaluation.application.dtos import EvaluationRunInput
from researchlens.modules.evaluation.application.evaluation_stage_steps import EvaluationStageSteps
from researchlens.shared.config.drafting import DraftingSettings
from researchlens.shared.config.evaluation import EvaluationSettings


class _RecordingCancellationProbe:
    def __init__(self) -> None:
        self.active_calls = 0
        self.max_active_calls = 0

    async def cancel_requested(self, *, run_id):  # type: ignore[no-untyped-def]
        self.active_calls += 1
        self.max_active_calls = max(self.max_active_calls, self.active_calls)
        await asyncio.sleep(0)
        self.active_calls -= 1
        return False


@pytest.mark.asyncio
async def test_drafting_stage_steps_serialize_cancellation_checks() -> None:
    probe = _RecordingCancellationProbe()
    steps = DraftingStageSteps(
        settings=DraftingSettings(),
        repository=None,  # type: ignore[arg-type]
        generation_client=None,  # type: ignore[arg-type]
        cancellation_probe=probe,  # type: ignore[arg-type]
        provider_name="openai",
    )

    run_id = uuid4()
    await asyncio.gather(
        steps._cancel_requested(run_id=run_id),
        steps._cancel_requested(run_id=run_id),
        steps._cancel_requested(run_id=run_id),
    )

    assert probe.max_active_calls == 1


@pytest.mark.asyncio
async def test_evaluation_stage_steps_serialize_cancellation_checks() -> None:
    probe = _RecordingCancellationProbe()
    steps = EvaluationStageSteps(
        settings=EvaluationSettings(),
        repository=None,  # type: ignore[arg-type]
        evaluator=None,  # type: ignore[arg-type]
        cancellation_probe=probe,  # type: ignore[arg-type]
    )
    run_input = EvaluationRunInput(
        tenant_id=uuid4(),
        run_id=uuid4(),
        research_question="Question",
        sections=(),
    )

    await asyncio.gather(
        steps._raise_if_canceled(run_input=run_input),
        steps._raise_if_canceled(run_input=run_input),
        steps._raise_if_canceled(run_input=run_input),
    )

    assert probe.max_active_calls == 1
