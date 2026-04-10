from typing import cast
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.projects.application.ports import ProjectRepository
from researchlens.modules.projects.domain import Project
from researchlens.modules.projects.infrastructure.mappers import to_domain, update_row
from researchlens.modules.projects.infrastructure.project_row import ProjectRow


class SqlAlchemyProjectRepository(ProjectRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, project: Project) -> Project:
        row = ProjectRow(
            id=project.id,
            tenant_id=project.tenant_id,
            name=project.name,
            description=project.description,
            created_by=project.created_by,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        self._session.add(row)
        await self._session.flush()
        return to_domain(row)

    async def get_by_id_for_tenant(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
    ) -> Project | None:
        row = await self._get_row_by_id_for_tenant(
            tenant_id=tenant_id,
            project_id=project_id,
        )
        if row is None:
            return None
        return to_domain(row)

    async def get_by_name_for_tenant(
        self,
        *,
        tenant_id: UUID,
        name: str,
    ) -> Project | None:
        statement = select(ProjectRow).where(
            ProjectRow.tenant_id == tenant_id,
            ProjectRow.name == name,
        )
        row = await self._session.scalar(statement)
        if row is None:
            return None
        return to_domain(row)

    async def list_by_tenant(self, *, tenant_id: UUID) -> list[Project]:
        statement = (
            select(ProjectRow)
            .where(ProjectRow.tenant_id == tenant_id)
            .order_by(ProjectRow.updated_at.desc(), ProjectRow.created_at.desc())
        )
        rows = await self._session.scalars(statement)
        return [to_domain(row) for row in rows]

    async def save(self, project: Project) -> Project | None:
        row = await self._get_row_by_id_for_tenant(
            tenant_id=project.tenant_id,
            project_id=project.id,
        )
        if row is None:
            return None

        update_row(row, project)
        await self._session.flush()
        return to_domain(row)

    async def delete_by_id_for_tenant(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
    ) -> bool:
        statement = delete(ProjectRow).where(
            ProjectRow.tenant_id == tenant_id,
            ProjectRow.id == project_id,
        )
        result = cast(CursorResult[object], await self._session.execute(statement))
        return bool(result.rowcount)

    async def _get_row_by_id_for_tenant(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
    ) -> ProjectRow | None:
        statement = select(ProjectRow).where(
            ProjectRow.tenant_id == tenant_id,
            ProjectRow.id == project_id,
        )
        row = await self._session.scalar(statement)
        return row if isinstance(row, ProjectRow) else None
