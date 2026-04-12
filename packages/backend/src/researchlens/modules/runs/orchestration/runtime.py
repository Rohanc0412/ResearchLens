from collections.abc import Callable
from uuid import UUID

from researchlens.modules.runs.application.ports import RunExecutionOrchestrator
from researchlens.modules.runs.domain import Run
from researchlens.modules.runs.orchestration.graph import build_run_graph
from researchlens.modules.runs.orchestration.runtime_bridge import RunGraphRuntimeBridge
from researchlens.modules.runs.orchestration.state import RunGraphState, initial_run_graph_state


class LangGraphRunOrchestrator(RunExecutionOrchestrator):
    def __init__(
        self,
        *,
        bridge: RunGraphRuntimeBridge,
        retrieval_subgraph_factory: Callable[[RunGraphState], object],
        drafting_subgraph_factory: Callable[[RunGraphState], object],
    ) -> None:
        self._bridge = bridge
        self._retrieval_subgraph_factory = retrieval_subgraph_factory
        self._drafting_subgraph_factory = drafting_subgraph_factory

    async def execute(
        self,
        *,
        run: Run,
        queue_item_id: UUID,
        lease_token: UUID,
    ) -> None:
        state = initial_run_graph_state(
            run_id=run.id,
            queue_item_id=queue_item_id,
            lease_token=lease_token,
        )
        graph = build_run_graph(
            bridge=self._bridge,
            retrieval_subgraph_factory=self._retrieval_subgraph_factory,
            drafting_subgraph_factory=self._drafting_subgraph_factory,
        )
        await graph.ainvoke(state)
