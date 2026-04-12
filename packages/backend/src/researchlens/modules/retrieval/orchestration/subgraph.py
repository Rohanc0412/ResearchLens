from collections.abc import Awaitable, Callable
from typing import Any, NotRequired, TypedDict, cast
from uuid import UUID

from langgraph.graph import END, START, StateGraph

from researchlens.modules.retrieval.application.retrieval_stage_steps import (
    RetrievalPlanningResult,
    RetrievalSelectionResult,
)
from researchlens.modules.retrieval.orchestration.graph_runtime import RetrievalGraphRuntime


class RetrievalGraphState(TypedDict):
    run_id: UUID
    request_text: str
    completed_stages: tuple[str, ...]
    retrieval_planning: NotRequired[RetrievalPlanningResult]
    retrieval_selection: NotRequired[RetrievalSelectionResult]
    retrieval_summary: NotRequired[Any]


RetrievalNode = Callable[[RetrievalGraphState], Awaitable[dict[str, object]]]


def build_retrieval_subgraph(runtime: RetrievalGraphRuntime) -> Any:
    graph = StateGraph(RetrievalGraphState)
    graph.add_node("plan_retrieval", cast(Any, _plan_retrieval(runtime)))
    graph.add_node("search_and_rank_sources", cast(Any, _search_and_rank_sources(runtime)))
    graph.add_node("persist_retrieval_outputs", cast(Any, _persist_retrieval_outputs(runtime)))
    graph.add_edge(START, "plan_retrieval")
    graph.add_edge("plan_retrieval", "search_and_rank_sources")
    graph.add_edge("search_and_rank_sources", "persist_retrieval_outputs")
    graph.add_edge("persist_retrieval_outputs", END)
    return graph.compile()


def _plan_retrieval(runtime: RetrievalGraphRuntime) -> RetrievalNode:
    async def node(state: RetrievalGraphState) -> dict[str, object]:
        question = str(state["request_text"])
        planning = await runtime.plan(question=question)
        return {
            "run_id": state["run_id"],
            "request_text": state["request_text"],
            "completed_stages": state.get("completed_stages", tuple()),
            "retrieval_planning": planning,
        }

    return node


def _search_and_rank_sources(runtime: RetrievalGraphRuntime) -> RetrievalNode:
    async def node(state: RetrievalGraphState) -> dict[str, object]:
        planning = state["retrieval_planning"]
        selection = await runtime.select_sources(
            planning=planning,
            question=str(state["request_text"]),
        )
        return {
            "run_id": state["run_id"],
            "request_text": state["request_text"],
            "completed_stages": state.get("completed_stages", tuple()),
            "retrieval_planning": planning,
            "retrieval_selection": selection,
        }

    return node


def _persist_retrieval_outputs(runtime: RetrievalGraphRuntime) -> RetrievalNode:
    async def node(state: RetrievalGraphState) -> dict[str, object]:
        completed_stages = tuple(str(item) for item in state["completed_stages"])
        summary = await runtime.finalize(
            run_id=state["run_id"],
            planning=state["retrieval_planning"],
            selection=state["retrieval_selection"],
            completed_stages=completed_stages,
        )
        return {
            "run_id": state["run_id"],
            "request_text": state["request_text"],
            "completed_stages": state["completed_stages"],
            "retrieval_summary": summary,
        }

    return node
