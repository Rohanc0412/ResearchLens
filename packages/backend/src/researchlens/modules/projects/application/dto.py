from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from researchlens.modules.projects.domain import Project


@dataclass(frozen=True, slots=True)
class ProjectView:
    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime


def to_project_view(project: Project) -> ProjectView:
    return ProjectView(
        id=project.id,
        tenant_id=project.tenant_id,
        name=project.name,
        description=project.description,
        created_by=project.created_by,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )
