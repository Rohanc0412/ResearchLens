from typing import Any
from uuid import UUID

from langgraph.graph import END, START, StateGraph

from researchlens.modules.drafting.orchestration.graph_runtime import DraftingGraphRuntime
from researchlens.shared.errors import CancellationRequestedError


def build_drafting_subgraph(runtime: DraftingGraphRuntime) -> Any:
    graph = StateGraph(dict)
    graph.add_node("prepare_draft_sections", _prepare_draft_sections(runtime))
    graph.add_node("draft_sections", _draft_sections(runtime))
    graph.add_node("assemble_report", _assemble_report(runtime))
    graph.add_edge(START, "prepare_draft_sections")
    graph.add_edge("prepare_draft_sections", "draft_sections")
    graph.add_edge("draft_sections", "assemble_report")
    graph.add_edge("assemble_report", END)
    return graph.compile()


def _prepare_draft_sections(runtime: DraftingGraphRuntime):
    async def node(state: dict[str, object]) -> dict[str, object]:
        prepared = await runtime.prepare(run_id=UUID(str(state["run_id"])))
        return {
            "run_id": state["run_id"],
            "completed_stages": state.get("completed_stages", tuple()),
            "drafting_prepared": prepared,
        }

    return node


def _draft_sections(runtime: DraftingGraphRuntime):
    async def node(state: dict[str, object]) -> dict[str, object]:
        prepared = state["drafting_prepared"]
        try:
            await runtime.draft_sections(prepared=prepared)
        except Exception as exc:
            await runtime.handle_failure(exc=exc)
            if isinstance(exc, CancellationRequestedError):
                return {
                    "run_id": state["run_id"],
                    "completed_stages": state.get("completed_stages", tuple()),
                    "drafting_prepared": prepared,
                    "terminal_status": "canceled",
                }
            raise
        return {
            "run_id": state["run_id"],
            "completed_stages": state.get("completed_stages", tuple()),
            "drafting_prepared": prepared,
        }

    return node


def _assemble_report(runtime: DraftingGraphRuntime):
    async def node(state: dict[str, object]) -> dict[str, object]:
        if state.get("terminal_status") == "canceled":
            return {
                "run_id": state["run_id"],
                "completed_stages": state.get("completed_stages", tuple()),
                "terminal_status": "canceled",
            }
        completed_stages = tuple(str(item) for item in state["completed_stages"])
        result = await runtime.assemble(
            prepared=state["drafting_prepared"],
            completed_stages=completed_stages,
        )
        return {
            "run_id": state["run_id"],
            "completed_stages": state["completed_stages"],
            "drafting_result": result,
        }

    return node
