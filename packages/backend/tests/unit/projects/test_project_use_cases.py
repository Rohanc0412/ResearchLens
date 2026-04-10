from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from researchlens.modules.projects.application import (
    CreateProjectCommand,
    CreateProjectUseCase,
    DeleteProjectCommand,
    DeleteProjectUseCase,
    ListProjectsQuery,
    ListProjectsUseCase,
    RenameProjectCommand,
    RenameProjectUseCase,
)
from researchlens.modules.projects.application.ports import ProjectRepository
from researchlens.modules.projects.domain import Project
from researchlens.shared.errors import ConflictError, NotFoundError


class InMemoryProjectRepository(ProjectRepository):
    def __init__(self, projects: list[Project] | None = None) -> None:
        self._projects = {project.id: project for project in projects or []}

    async def add(self, project: Project) -> Project:
        self._projects[project.id] = project
        return project

    async def get_by_id_for_tenant(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
    ) -> Project | None:
        project = self._projects.get(project_id)
        if project is None or project.tenant_id != tenant_id:
            return None
        return project

    async def get_by_name_for_tenant(
        self,
        *,
        tenant_id: UUID,
        name: str,
    ) -> Project | None:
        for project in self._projects.values():
            if project.tenant_id == tenant_id and project.name == name:
                return project
        return None

    async def list_by_tenant(self, *, tenant_id: UUID) -> list[Project]:
        projects = [
            project for project in self._projects.values() if project.tenant_id == tenant_id
        ]
        return sorted(projects, key=lambda item: (item.updated_at, item.created_at), reverse=True)

    async def save(self, project: Project) -> Project | None:
        if project.id not in self._projects:
            return None
        self._projects[project.id] = project
        return project

    async def delete_by_id_for_tenant(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
    ) -> bool:
        project = self._projects.get(project_id)
        if project is None or project.tenant_id != tenant_id:
            return False
        del self._projects[project_id]
        return True


class FakeTransactionManager:
    @asynccontextmanager
    async def boundary(self) -> AsyncIterator[None]:
        yield


def build_project(
    *,
    tenant_id: UUID,
    name: str,
    updated_at: datetime | None = None,
) -> Project:
    timestamp = datetime.now(tz=UTC)
    return Project.create(
        id=uuid4(),
        tenant_id=tenant_id,
        name=name,
        description=None,
        created_by="user-1",
        created_at=timestamp,
        updated_at=updated_at or timestamp,
    )


@pytest.mark.asyncio
async def test_create_project_success() -> None:
    tenant_id = uuid4()
    use_case = CreateProjectUseCase(InMemoryProjectRepository(), FakeTransactionManager())

    project = await use_case.execute(
        CreateProjectCommand(
            tenant_id=tenant_id,
            actor_user_id="user-1",
            name="  Alpha  ",
            description="demo",
        )
    )

    assert project.tenant_id == tenant_id
    assert project.name == "Alpha"
    assert project.description == "demo"


@pytest.mark.asyncio
async def test_create_project_duplicate_name_conflict() -> None:
    tenant_id = uuid4()
    repository = InMemoryProjectRepository([build_project(tenant_id=tenant_id, name="Alpha")])
    use_case = CreateProjectUseCase(repository, FakeTransactionManager())

    with pytest.raises(ConflictError):
        await use_case.execute(
            CreateProjectCommand(
                tenant_id=tenant_id,
                actor_user_id="user-1",
                name="Alpha",
                description=None,
            )
        )


@pytest.mark.asyncio
async def test_list_projects_orders_by_updated_then_created_desc() -> None:
    tenant_id = uuid4()
    now = datetime.now(tz=UTC)
    older = build_project(tenant_id=tenant_id, name="Older", updated_at=now - timedelta(days=2))
    newest = build_project(tenant_id=tenant_id, name="Newest", updated_at=now)
    middle = replace(
        build_project(tenant_id=tenant_id, name="Middle", updated_at=now - timedelta(days=1)),
        created_at=now - timedelta(hours=12),
    )
    use_case = ListProjectsUseCase(InMemoryProjectRepository([older, middle, newest]))

    projects = await use_case.execute(ListProjectsQuery(tenant_id=tenant_id))

    assert [project.name for project in projects] == ["Newest", "Middle", "Older"]


@pytest.mark.asyncio
async def test_rename_project_success() -> None:
    tenant_id = uuid4()
    project = build_project(tenant_id=tenant_id, name="Alpha")
    use_case = RenameProjectUseCase(
        InMemoryProjectRepository([project]),
        FakeTransactionManager(),
    )

    renamed = await use_case.execute(
        RenameProjectCommand(
            tenant_id=tenant_id,
            actor_user_id="user-1",
            project_id=project.id,
            new_name="Beta",
        )
    )

    assert renamed.name == "Beta"
    assert renamed.updated_at >= project.updated_at


@pytest.mark.asyncio
async def test_rename_project_duplicate_name_conflict() -> None:
    tenant_id = uuid4()
    source = build_project(tenant_id=tenant_id, name="Alpha")
    target = build_project(tenant_id=tenant_id, name="Beta")
    use_case = RenameProjectUseCase(
        InMemoryProjectRepository([source, target]),
        FakeTransactionManager(),
    )

    with pytest.raises(ConflictError):
        await use_case.execute(
            RenameProjectCommand(
                tenant_id=tenant_id,
                actor_user_id="user-1",
                project_id=source.id,
                new_name="Beta",
            )
        )


@pytest.mark.asyncio
async def test_rename_project_not_found() -> None:
    use_case = RenameProjectUseCase(InMemoryProjectRepository(), FakeTransactionManager())

    with pytest.raises(NotFoundError):
        await use_case.execute(
            RenameProjectCommand(
                tenant_id=uuid4(),
                actor_user_id="user-1",
                project_id=uuid4(),
                new_name="Beta",
            )
        )


@pytest.mark.asyncio
async def test_rename_project_same_name_is_no_op() -> None:
    tenant_id = uuid4()
    project = build_project(tenant_id=tenant_id, name="Alpha")
    use_case = RenameProjectUseCase(
        InMemoryProjectRepository([project]),
        FakeTransactionManager(),
    )

    renamed = await use_case.execute(
        RenameProjectCommand(
            tenant_id=tenant_id,
            actor_user_id="user-1",
            project_id=project.id,
            new_name="  Alpha  ",
        )
    )

    assert renamed.name == "Alpha"
    assert renamed.updated_at == project.updated_at


@pytest.mark.asyncio
async def test_delete_project_success() -> None:
    tenant_id = uuid4()
    project = build_project(tenant_id=tenant_id, name="Alpha")
    repository = InMemoryProjectRepository([project])
    use_case = DeleteProjectUseCase(repository, FakeTransactionManager())

    await use_case.execute(
        DeleteProjectCommand(
            tenant_id=tenant_id,
            actor_user_id="user-1",
            project_id=project.id,
        )
    )

    assert await repository.get_by_id_for_tenant(tenant_id=tenant_id, project_id=project.id) is None


@pytest.mark.asyncio
async def test_delete_project_not_found() -> None:
    use_case = DeleteProjectUseCase(InMemoryProjectRepository(), FakeTransactionManager())

    with pytest.raises(NotFoundError):
        await use_case.execute(
            DeleteProjectCommand(
                tenant_id=uuid4(),
                actor_user_id="user-1",
                project_id=uuid4(),
            )
        )
