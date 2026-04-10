from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from researchlens.modules.projects.application import (
    CreateProjectUseCase,
    DeleteProjectUseCase,
    ListProjectsUseCase,
    RenameProjectUseCase,
)
from researchlens.modules.projects.infrastructure.project_repository_sql import (
    SqlAlchemyProjectRepository,
)
from researchlens.shared.db import SqlAlchemyTransactionManager


class ProjectsRequestContext:
    def __init__(self, session: AsyncSession) -> None:
        repository = SqlAlchemyProjectRepository(session)
        transaction_manager = SqlAlchemyTransactionManager(session)
        self.create_project = CreateProjectUseCase(repository, transaction_manager)
        self.list_projects = ListProjectsUseCase(repository)
        self.rename_project = RenameProjectUseCase(repository, transaction_manager)
        self.delete_project = DeleteProjectUseCase(repository, transaction_manager)


class SqlAlchemyProjectsRuntime:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @asynccontextmanager
    async def request_context(self) -> AsyncIterator[ProjectsRequestContext]:
        async with self._session_factory() as session:
            yield ProjectsRequestContext(session)
