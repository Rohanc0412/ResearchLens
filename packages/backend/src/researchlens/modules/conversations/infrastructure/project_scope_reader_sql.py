from uuid import UUID

from sqlalchemy import column, select, table
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Uuid

from researchlens.modules.conversations.application.ports import ProjectScopeReader

projects_table = table(
    "projects",
    column("id", Uuid),
    column("tenant_id", Uuid),
)


class SqlAlchemyProjectScopeReader(ProjectScopeReader):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def project_exists_for_tenant(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
    ) -> bool:
        statement = select(projects_table.c.id).where(
            projects_table.c.tenant_id == tenant_id,
            projects_table.c.id == project_id,
        )
        return await self._session.scalar(statement) is not None
