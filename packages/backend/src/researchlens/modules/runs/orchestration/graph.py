from langgraph.graph import END, START, StateGraph

from researchlens.modules.runs.domain import RunStage
from researchlens.modules.runs.orchestration.runtime_bridge import RunGraphRuntimeBridge
from researchlens.modules.runs.orchestration.state import RunGraphState, restore_graph_state


def build_run_graph(
    *,
    bridge: RunGraphRuntimeBridge,
    retrieval_subgraph_factory: object,
    drafting_subgraph_factory: object,
) -> object:
    graph = StateGraph(RunGraphState)
    graph.add_node("load_run_context", _load_run_context(bridge))
    graph.add_node("restore_or_initialize_graph_state", _restore_graph_state())
    graph.add_node("maybe_resume_from_checkpoint", _maybe_resume_from_checkpoint(bridge))
    graph.add_node(
        "retrieval_subgraph",
        _run_stage_subgraph(bridge, RunStage.RETRIEVE, retrieval_subgraph_factory),
    )
    graph.add_node(
        "drafting_subgraph",
        _run_stage_subgraph(bridge, RunStage.DRAFT, drafting_subgraph_factory),
    )
    graph.add_node("finalize_run", _finalize_run(bridge))
    graph.add_edge(START, "load_run_context")
    graph.add_edge("load_run_context", "restore_or_initialize_graph_state")
    graph.add_edge("restore_or_initialize_graph_state", "maybe_resume_from_checkpoint")
    graph.add_conditional_edges(
        "maybe_resume_from_checkpoint",
        _route_from_resume,
        {
            "retrieval_subgraph": "retrieval_subgraph",
            "drafting_subgraph": "drafting_subgraph",
            "finalize_run": "finalize_run",
        },
    )
    graph.add_edge("retrieval_subgraph", "drafting_subgraph")
    graph.add_edge("drafting_subgraph", "finalize_run")
    graph.add_edge("finalize_run", END)
    return graph.compile()


def _load_run_context(bridge: RunGraphRuntimeBridge):
    async def node(state: RunGraphState) -> dict[str, object]:
        context = await bridge.load_context(run_id=state["run_id"])
        return {
            "loaded_run": context.run,
            "request_text": context.request_text,
            "latest_checkpoint": context.latest_checkpoint,
        }

    return node


def _restore_graph_state():
    async def node(state: RunGraphState) -> dict[str, object]:
        restored = restore_graph_state(
            run=state["loaded_run"],
            request_text=str(state["request_text"]),
            latest_checkpoint=state["latest_checkpoint"],
        )
        restored["queue_item_id"] = state["queue_item_id"]
        restored["lease_token"] = state["lease_token"]
        return restored

    return node


def _maybe_resume_from_checkpoint(bridge: RunGraphRuntimeBridge):
    async def node(state: RunGraphState) -> dict[str, object]:
        run = await bridge.mark_running(
            run=state["loaded_run"],
            start_stage=RunStage(state["start_stage"]),
        )
        return {
            "current_stage": run.current_stage.value if run.current_stage else None,
            "cancel_requested": run.cancel_requested_at is not None,
        }

    return node


def _run_stage_subgraph(bridge: RunGraphRuntimeBridge, stage: RunStage, subgraph_factory: object):
    async def node(state: RunGraphState) -> dict[str, object]:
        if state.get("terminal_status") == "canceled":
            return {}
        if stage.value in state["completed_stages"]:
            return {}
        if stage == RunStage.RETRIEVE and state["start_stage"] != RunStage.RETRIEVE.value:
            return {}
        if (
            stage == RunStage.DRAFT
            and state.get("current_stage") != RunStage.DRAFT.value
            and state["start_stage"] != RunStage.DRAFT.value
        ):
            return {}
        if not await bridge.stage_entered(state=state, stage=stage):
            return {"terminal_status": "canceled"}
        result = await subgraph_factory(state).ainvoke(state)
        state.update(result)
        if state.get("terminal_status") == "canceled":
            return {"terminal_status": "canceled"}
        await bridge.stage_completed(state=state, stage=stage)
        return state

    return node


def _finalize_run(bridge: RunGraphRuntimeBridge):
    async def node(state: RunGraphState) -> dict[str, object]:
        await bridge.finalize(state=state)
        return {}

    return node


def _route_from_resume(state: RunGraphState) -> str:
    if state.get("terminal_status") == "canceled":
        return "finalize_run"
    if state["start_stage"] == RunStage.DRAFT.value:
        return "drafting_subgraph"
    if state["start_stage"] == RunStage.RETRIEVE.value:
        return "retrieval_subgraph"
    return "finalize_run"
