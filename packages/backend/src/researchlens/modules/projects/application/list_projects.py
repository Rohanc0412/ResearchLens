from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.projects.application.dto import ProjectView, to_project_view
from researchlens.modules.projects.application.ports import ProjectRepository


@dataclass(frozen=True, slots=True)
class ListProjectsQuery:
    tenant_id: UUID


class ListProjectsUseCase:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    async def execute(self, query: ListProjectsQuery) -> list[ProjectView]:
        projects = await self._repository.list_by_tenant(tenant_id=query.tenant_id)
        return [to_project_view(project) for project in projects]
