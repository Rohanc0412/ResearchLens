from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from researchlens.modules.projects.application import (
    GetProjectQuery,
    GetProjectUseCase,
    UpdateProjectMetadataCommand,
    UpdateProjectMetadataUseCase,
)
from researchlens.modules.projects.application.ports import ProjectRepository
from researchlens.modules.projects.domain import Project
from researchlens.shared.errors import ConflictError, NotFoundError, ValidationError


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
        return [project for project in self._projects.values() if project.tenant_id == tenant_id]

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


def build_project(*, tenant_id: UUID, name: str) -> Project:
    timestamp = datetime.now(tz=UTC)
    return Project.create(
        id=uuid4(),
        tenant_id=tenant_id,
        name=name,
        description=None,
        created_by="user-1",
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.mark.asyncio
async def test_get_project_returns_details() -> None:
    tenant_id = uuid4()
    project = build_project(tenant_id=tenant_id, name="Alpha")
    use_case = GetProjectUseCase(InMemoryProjectRepository([project]))

    view = await use_case.execute(GetProjectQuery(tenant_id=tenant_id, project_id=project.id))

    assert view.id == project.id
    assert view.name == "Alpha"


@pytest.mark.asyncio
async def test_update_project_metadata_changes_description_without_renaming() -> None:
    tenant_id = uuid4()
    project = build_project(tenant_id=tenant_id, name="Alpha")
    use_case = UpdateProjectMetadataUseCase(
        InMemoryProjectRepository([project]),
        FakeTransactionManager(),
    )

    updated = await use_case.execute(
        UpdateProjectMetadataCommand(
            tenant_id=tenant_id,
            actor_user_id="user-1",
            project_id=project.id,
            new_name=None,
            description="  Updated summary  ",
            description_provided=True,
        )
    )

    assert updated.name == "Alpha"
    assert updated.description == "Updated summary"
    assert updated.updated_at >= project.updated_at


@pytest.mark.asyncio
async def test_update_project_metadata_same_values_is_no_op() -> None:
    tenant_id = uuid4()
    timestamp = datetime.now(tz=UTC)
    project = build_project(tenant_id=tenant_id, name="Alpha")
    project = project.update_metadata(
        new_name=None,
        new_description="demo",
        description_provided=True,
        updated_at=timestamp,
    )
    use_case = UpdateProjectMetadataUseCase(
        InMemoryProjectRepository([project]),
        FakeTransactionManager(),
    )

    updated = await use_case.execute(
        UpdateProjectMetadataCommand(
            tenant_id=tenant_id,
            actor_user_id="user-1",
            project_id=project.id,
            new_name=" Alpha ",
            description="demo",
            description_provided=True,
        )
    )

    assert updated.updated_at == project.updated_at


@pytest.mark.asyncio
async def test_update_project_metadata_rejects_duplicate_name() -> None:
    tenant_id = uuid4()
    source = build_project(tenant_id=tenant_id, name="Alpha")
    target = build_project(tenant_id=tenant_id, name="Beta")
    use_case = UpdateProjectMetadataUseCase(
        InMemoryProjectRepository([source, target]),
        FakeTransactionManager(),
    )

    with pytest.raises(ConflictError):
        await use_case.execute(
            UpdateProjectMetadataCommand(
                tenant_id=tenant_id,
                actor_user_id="user-1",
                project_id=source.id,
                new_name="Beta",
                description=None,
                description_provided=False,
            )
        )


@pytest.mark.asyncio
async def test_update_project_metadata_requires_at_least_one_field() -> None:
    tenant_id = uuid4()
    project = build_project(tenant_id=tenant_id, name="Alpha")
    use_case = UpdateProjectMetadataUseCase(
        InMemoryProjectRepository([project]),
        FakeTransactionManager(),
    )

    with pytest.raises(ValidationError):
        await use_case.execute(
            UpdateProjectMetadataCommand(
                tenant_id=tenant_id,
                actor_user_id="user-1",
                project_id=project.id,
                new_name=None,
                description=None,
                description_provided=False,
            )
        )


@pytest.mark.asyncio
async def test_get_project_raises_not_found_for_other_tenant() -> None:
    project = build_project(tenant_id=uuid4(), name="Alpha")
    use_case = GetProjectUseCase(InMemoryProjectRepository([project]))

    with pytest.raises(NotFoundError):
        await use_case.execute(GetProjectQuery(tenant_id=uuid4(), project_id=project.id))
