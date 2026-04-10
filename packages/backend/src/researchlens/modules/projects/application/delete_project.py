import logging
from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.projects.application.ports import ProjectRepository, TransactionManager
from researchlens.shared.errors import NotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DeleteProjectCommand:
    tenant_id: UUID
    actor_user_id: str
    project_id: UUID


class DeleteProjectUseCase:
    def __init__(
        self,
        repository: ProjectRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager

    async def execute(self, command: DeleteProjectCommand) -> None:
        async with self._transaction_manager.boundary():
            deleted = await self._repository.delete_by_id_for_tenant(
                tenant_id=command.tenant_id,
                project_id=command.project_id,
            )
            if not deleted:
                raise NotFoundError("Project was not found.")

        logger.info("project deleted project_id=%s", command.project_id)
