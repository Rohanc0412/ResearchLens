from datetime import UTC, datetime
from uuid import uuid4

import pytest

from researchlens.modules.projects.domain import Project
from researchlens.modules.projects.infrastructure import SqlAlchemyProjectRepository
from researchlens.shared.db import session_scope


@pytest.mark.asyncio
async def test_repository_create_list_rename_delete(database_runtime) -> None:
    tenant_id = uuid4()
    async with session_scope(database_runtime.session_factory) as session:
        repository = SqlAlchemyProjectRepository(session)
        project = Project.create(
            id=uuid4(),
            tenant_id=tenant_id,
            name="Alpha",
            description="demo",
            created_by="user-1",
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )

        created = await repository.add(project)
        await session.commit()

    async with session_scope(database_runtime.session_factory) as session:
        repository = SqlAlchemyProjectRepository(session)
        projects = await repository.list_by_tenant(tenant_id=tenant_id)
        renamed = await repository.save(
            Project.create(
                id=created.id,
                tenant_id=created.tenant_id,
                name="Beta",
                description=created.description,
                created_by=created.created_by,
                created_at=created.created_at,
                updated_at=datetime.now(tz=UTC),
            )
        )
        await session.commit()

    assert [project.name for project in projects] == ["Alpha"]
    assert renamed is not None
    assert renamed.name == "Beta"

    async with session_scope(database_runtime.session_factory) as session:
        repository = SqlAlchemyProjectRepository(session)
        deleted = await repository.delete_by_id_for_tenant(
            tenant_id=tenant_id,
            project_id=created.id,
        )
        await session.commit()

    assert deleted is True


@pytest.mark.asyncio
async def test_repository_scopes_by_tenant(database_runtime) -> None:
    tenant_id = uuid4()
    other_tenant_id = uuid4()
    project = Project.create(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Alpha",
        description=None,
        created_by="user-1",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    async with session_scope(database_runtime.session_factory) as session:
        repository = SqlAlchemyProjectRepository(session)
        await repository.add(project)
        await session.commit()

    async with session_scope(database_runtime.session_factory) as session:
        repository = SqlAlchemyProjectRepository(session)
        fetched = await repository.get_by_id_for_tenant(
            tenant_id=other_tenant_id,
            project_id=project.id,
        )

    assert fetched is None
