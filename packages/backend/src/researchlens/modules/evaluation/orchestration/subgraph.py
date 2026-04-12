from collections.abc import Awaitable, Callable
from typing import Any, NotRequired, TypedDict, cast
from uuid import UUID

from langgraph.graph import END, START, StateGraph

from researchlens.modules.evaluation.application import (
    EvaluationExecutionResult,
    EvaluationPassRecord,
    EvaluationRunInput,
    EvaluationSummary,
)
from researchlens.modules.evaluation.orchestration.graph_runtime import EvaluationGraphRuntime
from researchlens.shared.errors import CancellationRequestedError


class EvaluationGraphState(TypedDict):
    run_id: UUID
    completed_stages: tuple[str, ...]
    terminal_status: NotRequired[str]
    evaluation_input: NotRequired[EvaluationRunInput]
    evaluation_pass: NotRequired[EvaluationPassRecord]
    evaluation_results: NotRequired[EvaluationExecutionResult]
    evaluation_summary: NotRequired[EvaluationSummary]
    sections_requiring_repair: NotRequired[tuple[str, ...]]
    repair_recommended: NotRequired[bool]
    evaluation_status: NotRequired[str]


EvaluationNode = Callable[[EvaluationGraphState], Awaitable[dict[str, object]]]


def build_evaluation_subgraph(runtime: EvaluationGraphRuntime) -> Any:
    graph = StateGraph(EvaluationGraphState)
    graph.add_node("load_evaluation_inputs", cast(Any, _load_evaluation_inputs(runtime)))
    graph.add_node("create_evaluation_pass", cast(Any, _create_evaluation_pass(runtime)))
    graph.add_node("evaluate_sections", cast(Any, _evaluate_sections(runtime)))
    graph.add_node("persist_evaluation_results", cast(Any, _persist_evaluation_results(runtime)))
    graph.add_node("finalize_evaluation_metrics", cast(Any, _finalize_evaluation_metrics(runtime)))
    graph.add_node("checkpoint_evaluation", cast(Any, _checkpoint_evaluation(runtime)))
    graph.add_edge(START, "load_evaluation_inputs")
    graph.add_edge("load_evaluation_inputs", "create_evaluation_pass")
    graph.add_edge("create_evaluation_pass", "evaluate_sections")
    graph.add_edge("evaluate_sections", "persist_evaluation_results")
    graph.add_edge("persist_evaluation_results", "finalize_evaluation_metrics")
    graph.add_edge("finalize_evaluation_metrics", "checkpoint_evaluation")
    graph.add_edge("checkpoint_evaluation", END)
    return graph.compile()


def _load_evaluation_inputs(runtime: EvaluationGraphRuntime) -> EvaluationNode:
    async def node(state: EvaluationGraphState) -> dict[str, object]:
        evaluation_input = await runtime.load_inputs(run_id=state["run_id"])
        return {
            "run_id": state["run_id"],
            "completed_stages": state.get("completed_stages", tuple()),
            "evaluation_input": evaluation_input,
        }

    return node


def _create_evaluation_pass(runtime: EvaluationGraphRuntime) -> EvaluationNode:
    async def node(state: EvaluationGraphState) -> dict[str, object]:
        evaluation_pass = await runtime.create_pass(run_input=state["evaluation_input"])
        return {**state, "evaluation_pass": evaluation_pass}

    return node


def _evaluate_sections(runtime: EvaluationGraphRuntime) -> EvaluationNode:
    async def node(state: EvaluationGraphState) -> dict[str, object]:
        try:
            result = await runtime.evaluate_sections(
                run_input=state["evaluation_input"],
                evaluation_pass=state["evaluation_pass"],
            )
        except CancellationRequestedError:
            return {**state, "terminal_status": "canceled"}
        return {**state, "evaluation_results": result}

    return node


def _persist_evaluation_results(runtime: EvaluationGraphRuntime) -> EvaluationNode:
    async def node(state: EvaluationGraphState) -> dict[str, object]:
        if state.get("terminal_status") == "canceled":
            return dict(state)
        await runtime.persist_results(
            evaluation_pass=state["evaluation_pass"],
            section_results=state["evaluation_results"],
        )
        return dict(state)

    return node


def _finalize_evaluation_metrics(runtime: EvaluationGraphRuntime) -> EvaluationNode:
    async def node(state: EvaluationGraphState) -> dict[str, object]:
        if state.get("terminal_status") == "canceled":
            return dict(state)
        summary = await runtime.finalize(
            run_input=state["evaluation_input"],
            evaluation_pass=state["evaluation_pass"],
            section_results=state["evaluation_results"],
        )
        return {
            **state,
            "evaluation_summary": summary,
            "sections_requiring_repair": summary.sections_requiring_repair,
            "repair_recommended": summary.repair_recommended,
            "evaluation_status": "completed",
        }

    return node


def _checkpoint_evaluation(runtime: EvaluationGraphRuntime) -> EvaluationNode:
    async def node(state: EvaluationGraphState) -> dict[str, object]:
        if state.get("terminal_status") == "canceled":
            return dict(state)
        await runtime.checkpoint(
            summary=state["evaluation_summary"],
            completed_stages=state["completed_stages"],
        )
        return dict(state)

    return node
