from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.projects.application.dto import ProjectView, to_project_view
from researchlens.modules.projects.application.ports import ProjectRepository
from researchlens.shared.errors import NotFoundError


@dataclass(frozen=True, slots=True)
class GetProjectQuery:
    tenant_id: UUID
    project_id: UUID


class GetProjectUseCase:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    async def execute(self, query: GetProjectQuery) -> ProjectView:
        project = await self._repository.get_by_id_for_tenant(
            tenant_id=query.tenant_id,
            project_id=query.project_id,
        )
        if project is None:
            raise NotFoundError("Project was not found.")
        return to_project_view(project)
