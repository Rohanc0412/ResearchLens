from typing import Protocol
from uuid import UUID

from researchlens.modules.repair.infrastructure import SqlAlchemyRepairRepository
from researchlens.modules.runs.orchestration.state import RunGraphState


class _CompiledGraph(Protocol):
    async def ainvoke(self, state: object) -> RunGraphState: ...


class RepairReevaluationSubgraph:
    def __init__(
        self,
        *,
        evaluation_graph: _CompiledGraph,
        repair_repository: SqlAlchemyRepairRepository,
    ) -> None:
        self._evaluation_graph = evaluation_graph
        self._repair_repository = repair_repository

    async def ainvoke(self, state: object) -> RunGraphState:
        result = await self._evaluation_graph.ainvoke(state)
        summary = result.get("evaluation_summary")
        changed = tuple(str(item) for item in result.get("target_section_ids", ()))
        if summary is not None and changed:
            await self._repair_repository.link_reevaluation_pass(
                run_id=UUID(str(result["run_id"])),
                changed_section_ids=changed,
                reevaluation_pass_id=summary.evaluation_pass_id,
            )
        return result
