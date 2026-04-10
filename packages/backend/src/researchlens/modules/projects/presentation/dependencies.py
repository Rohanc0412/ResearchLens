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
from researchlens.shared.errors import AuthenticationError
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


class AuthenticatedActor(Protocol):
    tenant_id: UUID
    user_id: UUID
    roles: list[str]


class AuthRuntime(Protocol):
    async def resolve_actor(self, *, access_token: str) -> AuthenticatedActor: ...


async def get_projects_context(request: Request) -> AsyncIterator[ProjectsRequestContext]:
    runtime = cast(ProjectsRuntime, request.app.state.bootstrap.projects_runtime)
    async with runtime.request_context() as context:
        yield context


async def get_request_actor(request: Request) -> AsyncIterator[RequestActor]:
    auth_runtime = cast(AuthRuntime, request.app.state.bootstrap.auth_runtime)
    actor_identity = await auth_runtime.resolve_actor(
        access_token=_extract_bearer_token(request),
    )
    actor = RequestActor(
        tenant_id=actor_identity.tenant_id,
        user_id=str(actor_identity.user_id),
    )
    token = bind_tenant_id(str(actor.tenant_id))
    try:
        yield actor
    finally:
        reset_tenant_id(token)


ProjectsContext = Annotated[ProjectsRequestContext, Depends(get_projects_context)]


def _extract_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise AuthenticationError("Bearer access token is required.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationError("Bearer access token is required.")
    return token


def get_create_project_use_case(context: ProjectsContext) -> CreateProjectUseCase:
    return context.create_project


def get_list_projects_use_case(context: ProjectsContext) -> ListProjectsUseCase:
    return context.list_projects


def get_rename_project_use_case(context: ProjectsContext) -> RenameProjectUseCase:
    return context.rename_project


def get_delete_project_use_case(context: ProjectsContext) -> DeleteProjectUseCase:
    return context.delete_project
