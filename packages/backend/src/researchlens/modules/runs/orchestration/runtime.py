from uuid import UUID

from researchlens.modules.runs.application.ports import RunExecutionOrchestrator
from researchlens.modules.runs.domain import Run
from researchlens.modules.runs.orchestration.graph import StageSubgraphFactory, build_run_graph
from researchlens.modules.runs.orchestration.runtime_bridge import RunGraphRuntimeBridge
from researchlens.modules.runs.orchestration.state import initial_run_graph_state


class LangGraphRunOrchestrator(RunExecutionOrchestrator):
    def __init__(
        self,
        *,
        bridge: RunGraphRuntimeBridge,
        retrieval_subgraph_factory: StageSubgraphFactory,
        drafting_subgraph_factory: StageSubgraphFactory,
        evaluation_subgraph_factory: StageSubgraphFactory,
        repair_subgraph_factory: StageSubgraphFactory,
        reevaluation_subgraph_factory: StageSubgraphFactory,
    ) -> None:
        self._bridge = bridge
        self._retrieval_subgraph_factory = retrieval_subgraph_factory
        self._drafting_subgraph_factory = drafting_subgraph_factory
        self._evaluation_subgraph_factory = evaluation_subgraph_factory
        self._repair_subgraph_factory = repair_subgraph_factory
        self._reevaluation_subgraph_factory = reevaluation_subgraph_factory

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
            evaluation_subgraph_factory=self._evaluation_subgraph_factory,
            repair_subgraph_factory=self._repair_subgraph_factory,
            reevaluation_subgraph_factory=self._reevaluation_subgraph_factory,
        )
        await graph.ainvoke(state)
