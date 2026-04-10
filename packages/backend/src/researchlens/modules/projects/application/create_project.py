import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from researchlens.modules.projects.application.dto import ProjectView, to_project_view
from researchlens.modules.projects.application.ports import ProjectRepository, TransactionManager
from researchlens.modules.projects.domain import Project, normalize_project_name
from researchlens.shared.errors import ConflictError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CreateProjectCommand:
    tenant_id: UUID
    actor_user_id: str
    name: str
    description: str | None


class CreateProjectUseCase:
    def __init__(
        self,
        repository: ProjectRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager

    async def execute(self, command: CreateProjectCommand) -> ProjectView:
        normalized_name = normalize_project_name(command.name)

        async with self._transaction_manager.boundary():
            existing_project = await self._repository.get_by_name_for_tenant(
                tenant_id=command.tenant_id,
                name=normalized_name,
            )
            if existing_project is not None:
                logger.warning("project create conflict name=%s", normalized_name)
                raise ConflictError("Project name already exists for this tenant.")

            timestamp = datetime.now(tz=UTC)
            project = Project.create(
                id=uuid4(),
                tenant_id=command.tenant_id,
                name=normalized_name,
                description=command.description,
                created_by=command.actor_user_id,
                created_at=timestamp,
                updated_at=timestamp,
            )
            created_project = await self._repository.add(project)

        logger.info("project created project_id=%s", created_project.id)
        return to_project_view(created_project)
