from contextlib import AbstractAsyncContextManager
from typing import Protocol
from uuid import UUID

from researchlens.modules.projects.domain import Project


class ProjectRepository(Protocol):
    async def add(self, project: Project) -> Project: ...

    async def get_by_id_for_tenant(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
    ) -> Project | None: ...

    async def get_by_name_for_tenant(
        self,
        *,
        tenant_id: UUID,
        name: str,
    ) -> Project | None: ...

    async def list_by_tenant(self, *, tenant_id: UUID) -> list[Project]: ...

    async def save(self, project: Project) -> Project | None: ...

    async def delete_by_id_for_tenant(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
    ) -> bool: ...


class TransactionManager(Protocol):
    def boundary(self) -> AbstractAsyncContextManager[None]: ...
