from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Annotated, Protocol, cast
from uuid import UUID

from fastapi import Depends, Request

from researchlens.modules.projects.application import (
    CreateProjectUseCase,
    DeleteProjectUseCase,
    ListProjectsUseCase,
    RenameProjectUseCase,
)
from researchlens.shared.logging import bind_tenant_id, reset_tenant_id


@dataclass(frozen=True, slots=True)
class RequestActor:
    tenant_id: UUID
    user_id: str


class ProjectsRequestContext(Protocol):
    create_project: CreateProjectUseCase
    list_projects: ListProjectsUseCase
    rename_project: RenameProjectUseCase
    delete_project: DeleteProjectUseCase


class ProjectsRuntime(Protocol):
    def request_context(self) -> AbstractAsyncContextManager[ProjectsRequestContext]: ...


async def get_projects_context(request: Request) -> AsyncIterator[ProjectsRequestContext]:
    runtime = cast(ProjectsRuntime, request.app.state.bootstrap.projects_runtime)
    async with runtime.request_context() as context:
        yield context


async def get_request_actor(request: Request) -> AsyncIterator[RequestActor]:
    actor_settings = request.app.state.bootstrap.settings.bootstrap_actor
    actor = RequestActor(
        tenant_id=actor_settings.tenant_id,
        user_id=actor_settings.user_id,
    )
    token = bind_tenant_id(str(actor.tenant_id))
    try:
        yield actor
    finally:
        reset_tenant_id(token)


ProjectsContext = Annotated[ProjectsRequestContext, Depends(get_projects_context)]


def get_create_project_use_case(context: ProjectsContext) -> CreateProjectUseCase:
    return context.create_project


def get_list_projects_use_case(context: ProjectsContext) -> ListProjectsUseCase:
    return context.list_projects


def get_rename_project_use_case(context: ProjectsContext) -> RenameProjectUseCase:
    return context.rename_project


def get_delete_project_use_case(context: ProjectsContext) -> DeleteProjectUseCase:
    return context.delete_project
