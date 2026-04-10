import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from researchlens.modules.projects.application.dto import ProjectView, to_project_view
from researchlens.modules.projects.application.ports import ProjectRepository, TransactionManager
from researchlens.modules.projects.domain import (
    normalize_project_description,
    normalize_project_name,
)
from researchlens.shared.errors import ConflictError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class UpdateProjectMetadataCommand:
    tenant_id: UUID
    actor_user_id: str
    project_id: UUID
    new_name: str | None
    description: str | None
    description_provided: bool


class UpdateProjectMetadataUseCase:
    def __init__(
        self,
        repository: ProjectRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager

    async def execute(self, command: UpdateProjectMetadataCommand) -> ProjectView:
        if command.new_name is None and not command.description_provided:
            raise ValidationError("At least one project field must be provided.")

        normalized_name = None
        if command.new_name is not None:
            normalized_name = normalize_project_name(command.new_name)

        normalized_description = None
        if command.description_provided:
            normalized_description = normalize_project_description(command.description)

        async with self._transaction_manager.boundary():
            project = await self._repository.get_by_id_for_tenant(
                tenant_id=command.tenant_id,
                project_id=command.project_id,
            )
            if project is None:
                raise NotFoundError("Project was not found.")

            if normalized_name is not None and normalized_name != project.name:
                conflicting_project = await self._repository.get_by_name_for_tenant(
                    tenant_id=command.tenant_id,
                    name=normalized_name,
                )
                if conflicting_project is not None and conflicting_project.id != project.id:
                    logger.warning(
                        "project.update conflict tenant_id=%s user_id=%s project_id=%s name=%s",
                        command.tenant_id,
                        command.actor_user_id,
                        command.project_id,
                        normalized_name,
                    )
                    raise ConflictError("Project name already exists for this tenant.")

            if normalized_name in (None, project.name) and (
                not command.description_provided or normalized_description == project.description
            ):
                return to_project_view(project)

            updated_project = project.update_metadata(
                new_name=normalized_name,
                new_description=normalized_description,
                description_provided=command.description_provided,
                updated_at=datetime.now(tz=UTC),
            )
            saved_project = await self._repository.save(updated_project)
            if saved_project is None:
                raise NotFoundError("Project was not found.")

        logger.info(
            "project.update tenant_id=%s user_id=%s project_id=%s",
            command.tenant_id,
            command.actor_user_id,
            command.project_id,
        )
        return to_project_view(saved_project)
