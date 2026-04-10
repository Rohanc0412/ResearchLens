from researchlens.modules.projects.domain import Project
from researchlens.modules.projects.infrastructure.project_row import ProjectRow


def to_domain(row: ProjectRow) -> Project:
    return Project.create(
        id=row.id,
        tenant_id=row.tenant_id,
        name=row.name,
        description=row.description,
        created_by=row.created_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def update_row(row: ProjectRow, project: Project) -> None:
    row.name = project.name
    row.description = project.description
    row.updated_at = project.updated_at
