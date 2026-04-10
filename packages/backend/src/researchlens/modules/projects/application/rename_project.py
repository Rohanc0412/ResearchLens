import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from researchlens.modules.projects.application.dto import ProjectView, to_project_view
from researchlens.modules.projects.application.ports import ProjectRepository, TransactionManager
from researchlens.modules.projects.domain import normalize_project_name
from researchlens.shared.errors import ConflictError, NotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RenameProjectCommand:
    tenant_id: UUID
    actor_user_id: str
    project_id: UUID
    new_name: str


class RenameProjectUseCase:
    def __init__(
        self,
        repository: ProjectRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager

    async def execute(self, command: RenameProjectCommand) -> ProjectView:
        normalized_name = normalize_project_name(command.new_name)

        async with self._transaction_manager.boundary():
            project = await self._repository.get_by_id_for_tenant(
                tenant_id=command.tenant_id,
                project_id=command.project_id,
            )
            if project is None:
                raise NotFoundError("Project was not found.")

            if project.name == normalized_name:
                return to_project_view(project)

            conflicting_project = await self._repository.get_by_name_for_tenant(
                tenant_id=command.tenant_id,
                name=normalized_name,
            )
            if conflicting_project is not None and conflicting_project.id != project.id:
                logger.warning("project rename conflict name=%s", normalized_name)
                raise ConflictError("Project name already exists for this tenant.")

            renamed_project = project.rename(
                new_name=normalized_name,
                updated_at=datetime.now(tz=UTC),
            )
            saved_project = await self._repository.save(renamed_project)
            if saved_project is None:
                raise NotFoundError("Project was not found.")

        logger.info("project renamed project_id=%s", saved_project.id)
        return to_project_view(saved_project)
