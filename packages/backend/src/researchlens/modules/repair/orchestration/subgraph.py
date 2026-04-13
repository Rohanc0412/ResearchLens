from collections.abc import Awaitable, Callable
from typing import Any, NotRequired, TypedDict, cast
from uuid import UUID

from langgraph.graph import END, START, StateGraph

from researchlens.modules.repair.application import RepairExecutionSummary
from researchlens.modules.repair.orchestration.graph_runtime import RepairGraphRuntime
from researchlens.shared.errors import CancellationRequestedError


class RepairGraphState(TypedDict):
    run_id: UUID
    completed_stages: tuple[str, ...]
    terminal_status: NotRequired[str]
    repair_summary: NotRequired[RepairExecutionSummary]
    repair_recommended: NotRequired[bool]
    repaired_section_ids: NotRequired[tuple[str, ...]]
    repair_result_ids_by_section: NotRequired[dict[str, UUID]]


RepairNode = Callable[[RepairGraphState], Awaitable[dict[str, object]]]


def build_repair_subgraph(runtime: RepairGraphRuntime) -> Any:
    graph = StateGraph(RepairGraphState)
    graph.add_node("repair_sections", cast(Any, _repair_sections(runtime)))
    graph.add_node("checkpoint_repair", cast(Any, _checkpoint_repair(runtime)))
    graph.add_edge(START, "repair_sections")
    graph.add_edge("repair_sections", "checkpoint_repair")
    graph.add_edge("checkpoint_repair", END)
    return graph.compile()


def _repair_sections(runtime: RepairGraphRuntime) -> RepairNode:
    async def node(state: RepairGraphState) -> dict[str, object]:
        try:
            summary = await runtime.repair(run_id=state["run_id"])
        except CancellationRequestedError:
            return {**state, "terminal_status": "canceled"}
        return {
            **state,
            "repair_summary": summary,
            "repaired_section_ids": summary.changed_section_ids,
            "repair_result_ids_by_section": summary.result_ids_by_section,
            "repair_recommended": False,
        }

    return node


def _checkpoint_repair(runtime: RepairGraphRuntime) -> RepairNode:
    async def node(state: RepairGraphState) -> dict[str, object]:
        if state.get("terminal_status") == "canceled":
            return dict(state)
        await runtime.checkpoint(
            summary=state["repair_summary"],
            completed_stages=state["completed_stages"],
        )
        return dict(state)

    return node
