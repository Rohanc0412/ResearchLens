from typing import cast

import pytest

from researchlens.modules.runs.domain import RunStage
from researchlens.modules.runs.orchestration.graph import (
    _route_after_evaluation,
    _route_after_repair,
    _run_stage_subgraph,
)
from researchlens.modules.runs.orchestration.state import RunGraphState


def test_route_after_evaluation_exports_when_repair_is_not_recommended() -> None:
    state = cast(RunGraphState, {"repair_recommended": False})

    assert _route_after_evaluation(state) == "artifact_export_subgraph"


def test_route_after_evaluation_repairs_when_repair_is_recommended() -> None:
    state = cast(RunGraphState, {"repair_recommended": True})

    assert _route_after_evaluation(state) == "repair_subgraph"


def test_route_after_repair_exports_when_no_sections_changed() -> None:
    state = cast(RunGraphState, {"repaired_section_ids": ()})

    assert _route_after_repair(state) == "artifact_export_subgraph"


def test_route_after_repair_reevaluates_when_sections_changed() -> None:
    state = cast(RunGraphState, {"repaired_section_ids": ("S1",)})

    assert _route_after_repair(state) == "maybe_reevaluate_repaired_sections_subgraph"


@pytest.mark.asyncio
async def test_export_stage_runs_after_evaluation_when_repair_stage_is_current() -> None:
    bridge = _FakeBridge()
    node = _run_stage_subgraph(
        bridge,
        RunStage.EXPORT,
        lambda state: _FakeSubgraph(),
    )
    state = cast(
        RunGraphState,
        {
            "run_id": "00000000-0000-0000-0000-000000000001",
            "start_stage": "retrieve",
            "current_stage": "repair",
            "completed_stages": ("retrieve", "draft", "evaluate"),
        },
    )

    result = await node(state)

    assert bridge.entered == [RunStage.EXPORT]
    assert bridge.completed == [RunStage.EXPORT]
    assert result["artifact_export_summary"] == {"artifact_count": 2}


class _FakeBridge:
    def __init__(self) -> None:
        self.entered: list[RunStage] = []
        self.completed: list[RunStage] = []

    async def stage_entered(self, *, state: RunGraphState, stage: RunStage) -> bool:
        self.entered.append(stage)
        return True

    async def stage_completed(self, *, state: RunGraphState, stage: RunStage) -> None:
        self.completed.append(stage)
        state["completed_stages"] = tuple((*state["completed_stages"], stage.value))
        state["current_stage"] = stage.value


class _FakeSubgraph:
    async def ainvoke(self, state: RunGraphState) -> RunGraphState:
        return cast(
            RunGraphState,
            {**state, "artifact_export_summary": {"artifact_count": 2}},
        )
