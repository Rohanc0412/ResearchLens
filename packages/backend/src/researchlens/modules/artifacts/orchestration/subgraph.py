from collections.abc import Awaitable, Callable
from typing import Any, NotRequired, TypedDict, cast
from uuid import UUID

from langgraph.graph import END, START, StateGraph

from researchlens.modules.artifacts.orchestration.graph_runtime import ArtifactExportGraphRuntime


class ArtifactExportGraphState(TypedDict):
    run_id: UUID
    completed_stages: tuple[str, ...]
    terminal_status: NotRequired[str]
    artifact_export_summary: NotRequired[Any]


ArtifactExportNode = Callable[[ArtifactExportGraphState], Awaitable[dict[str, object]]]


def build_artifact_export_subgraph(runtime: ArtifactExportGraphRuntime) -> Any:
    graph = StateGraph(ArtifactExportGraphState)
    graph.add_node("export_report_artifacts", cast(Any, _export_report_artifacts(runtime)))
    graph.add_edge(START, "export_report_artifacts")
    graph.add_edge("export_report_artifacts", END)
    return graph.compile()


def _export_report_artifacts(runtime: ArtifactExportGraphRuntime) -> ArtifactExportNode:
    async def node(state: ArtifactExportGraphState) -> dict[str, object]:
        if state.get("terminal_status") == "canceled":
            return {"terminal_status": "canceled"}
        result = await runtime.export(
            run_id=state["run_id"],
            completed_stages=tuple(str(item) for item in state["completed_stages"]),
        )
        return {
            "run_id": state["run_id"],
            "completed_stages": state["completed_stages"],
            "artifact_export_summary": result,
        }

    return node
