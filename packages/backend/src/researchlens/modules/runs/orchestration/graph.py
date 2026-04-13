from collections.abc import Awaitable, Callable
from typing import Any, Protocol, cast

from langgraph.graph import END, START, StateGraph

from researchlens.modules.runs.domain import RunStage
from researchlens.modules.runs.orchestration.runtime_bridge import RunGraphRuntimeBridge
from researchlens.modules.runs.orchestration.state import RunGraphState, restore_graph_state


class StageSubgraph(Protocol):
    async def ainvoke(self, state: RunGraphState) -> RunGraphState: ...


StageSubgraphFactory = Callable[[RunGraphState], StageSubgraph]
RunNode = Callable[[RunGraphState], Awaitable[dict[str, object]]]


def build_run_graph(
    *,
    bridge: RunGraphRuntimeBridge,
    retrieval_subgraph_factory: StageSubgraphFactory,
    drafting_subgraph_factory: StageSubgraphFactory,
    evaluation_subgraph_factory: StageSubgraphFactory,
    repair_subgraph_factory: StageSubgraphFactory,
    reevaluation_subgraph_factory: StageSubgraphFactory,
) -> Any:
    graph = StateGraph[RunGraphState](RunGraphState)
    _add_run_nodes(
        graph,
        bridge=bridge,
        retrieval_subgraph_factory=retrieval_subgraph_factory,
        drafting_subgraph_factory=drafting_subgraph_factory,
        evaluation_subgraph_factory=evaluation_subgraph_factory,
        repair_subgraph_factory=repair_subgraph_factory,
        reevaluation_subgraph_factory=reevaluation_subgraph_factory,
    )
    _add_run_edges(graph)
    return graph.compile()


def _add_run_nodes(
    graph: StateGraph[RunGraphState],
    *,
    bridge: RunGraphRuntimeBridge,
    retrieval_subgraph_factory: StageSubgraphFactory,
    drafting_subgraph_factory: StageSubgraphFactory,
    evaluation_subgraph_factory: StageSubgraphFactory,
    repair_subgraph_factory: StageSubgraphFactory,
    reevaluation_subgraph_factory: StageSubgraphFactory,
) -> None:
    graph.add_node("load_run_context", cast(Any, _load_run_context(bridge)))
    graph.add_node("restore_or_initialize_graph_state", cast(Any, _restore_graph_state()))
    graph.add_node(
        "maybe_resume_from_checkpoint",
        cast(Any, _maybe_resume_from_checkpoint(bridge)),
    )
    graph.add_node(
        "retrieval_subgraph",
        cast(Any, _run_stage_subgraph(bridge, RunStage.RETRIEVE, retrieval_subgraph_factory)),
    )
    graph.add_node(
        "drafting_subgraph",
        cast(Any, _run_stage_subgraph(bridge, RunStage.DRAFT, drafting_subgraph_factory)),
    )
    graph.add_node(
        "evaluation_subgraph",
        cast(Any, _run_stage_subgraph(bridge, RunStage.EVALUATE, evaluation_subgraph_factory)),
    )
    graph.add_node(
        "repair_subgraph",
        cast(Any, _run_stage_subgraph(bridge, RunStage.REPAIR, repair_subgraph_factory)),
    )
    graph.add_node(
        "maybe_reevaluate_repaired_sections_subgraph",
        cast(Any, _run_reevaluation_subgraph(reevaluation_subgraph_factory)),
    )
    graph.add_node("finalize_run", cast(Any, _finalize_run(bridge)))


def _add_run_edges(graph: StateGraph[RunGraphState]) -> None:
    graph.add_edge(START, "load_run_context")
    graph.add_edge("load_run_context", "restore_or_initialize_graph_state")
    graph.add_edge("restore_or_initialize_graph_state", "maybe_resume_from_checkpoint")
    graph.add_conditional_edges(
        "maybe_resume_from_checkpoint",
        _route_from_resume,
        {
            "retrieval_subgraph": "retrieval_subgraph",
            "drafting_subgraph": "drafting_subgraph",
            "evaluation_subgraph": "evaluation_subgraph",
            "repair_subgraph": "repair_subgraph",
            "finalize_run": "finalize_run",
        },
    )
    graph.add_edge("retrieval_subgraph", "drafting_subgraph")
    graph.add_edge("drafting_subgraph", "evaluation_subgraph")
    graph.add_conditional_edges(
        "evaluation_subgraph",
        _route_after_evaluation,
        {
            "repair_subgraph": "repair_subgraph",
            "finalize_run": "finalize_run",
        },
    )
    graph.add_conditional_edges(
        "repair_subgraph",
        _route_after_repair,
        {
            "maybe_reevaluate_repaired_sections_subgraph": (
                "maybe_reevaluate_repaired_sections_subgraph"
            ),
            "finalize_run": "finalize_run",
        },
    )
    graph.add_edge("maybe_reevaluate_repaired_sections_subgraph", "finalize_run")
    graph.add_edge("finalize_run", END)


def _load_run_context(bridge: RunGraphRuntimeBridge) -> RunNode:
    async def node(state: RunGraphState) -> dict[str, object]:
        context = await bridge.load_context(run_id=state["run_id"])
        return {
            "loaded_run": context.run,
            "request_text": context.request_text,
            "latest_checkpoint": context.latest_checkpoint,
        }

    return node


def _restore_graph_state() -> RunNode:
    async def node(state: RunGraphState) -> dict[str, object]:
        restored = restore_graph_state(
            run=state["loaded_run"],
            request_text=str(state["request_text"]),
            latest_checkpoint=state["latest_checkpoint"],
        )
        restored["queue_item_id"] = state["queue_item_id"]
        restored["lease_token"] = state["lease_token"]
        return dict(restored)

    return node


def _maybe_resume_from_checkpoint(bridge: RunGraphRuntimeBridge) -> RunNode:
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


def _run_stage_subgraph(
    bridge: RunGraphRuntimeBridge,
    stage: RunStage,
    subgraph_factory: StageSubgraphFactory,
) -> RunNode:
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
        if (
            stage == RunStage.EVALUATE
            and state.get("current_stage") != RunStage.EVALUATE.value
            and state["start_stage"] != RunStage.EVALUATE.value
        ):
            return {}
        if (
            stage == RunStage.REPAIR
            and state.get("current_stage") != RunStage.REPAIR.value
            and state["start_stage"] != RunStage.REPAIR.value
        ):
            return {}
        if not await bridge.stage_entered(state=state, stage=stage):
            return {"terminal_status": "canceled"}
        result = await subgraph_factory(state).ainvoke(state)
        state.update(result)
        if state.get("terminal_status") == "canceled":
            return {"terminal_status": "canceled"}
        await bridge.stage_completed(state=state, stage=stage)
        return dict(state)

    return node


def _run_reevaluation_subgraph(subgraph_factory: StageSubgraphFactory) -> RunNode:
    async def node(state: RunGraphState) -> dict[str, object]:
        if state.get("terminal_status") == "canceled":
            return {}
        changed = tuple(str(item) for item in state.get("repaired_section_ids", ()))
        if not changed:
            return {}
        result = await subgraph_factory(state).ainvoke(
            {
                **state,
                "target_section_ids": changed,
                "evaluation_scope": "repair_reevaluation",
            }
        )
        return dict(result)

    return node


def _finalize_run(bridge: RunGraphRuntimeBridge) -> RunNode:
    async def node(state: RunGraphState) -> dict[str, object]:
        await bridge.finalize(state=state)
        return {}

    return node


def _route_from_resume(state: RunGraphState) -> str:
    if state.get("terminal_status") == "canceled":
        return "finalize_run"
    if state["start_stage"] == RunStage.REPAIR.value:
        return "repair_subgraph"
    if state["start_stage"] == RunStage.DRAFT.value:
        return "drafting_subgraph"
    if state["start_stage"] == RunStage.EVALUATE.value:
        return "evaluation_subgraph"
    if state["start_stage"] == RunStage.RETRIEVE.value:
        return "retrieval_subgraph"
    return "finalize_run"


def _route_after_evaluation(state: RunGraphState) -> str:
    if state.get("terminal_status") == "canceled":
        return "finalize_run"
    return "repair_subgraph" if state.get("repair_recommended") is True else "finalize_run"


def _route_after_repair(state: RunGraphState) -> str:
    if state.get("terminal_status") == "canceled":
        return "finalize_run"
    return (
        "maybe_reevaluate_repaired_sections_subgraph"
        if tuple(state.get("repaired_section_ids", ()))
        else "finalize_run"
    )
