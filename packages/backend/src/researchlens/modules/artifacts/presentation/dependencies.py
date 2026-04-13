from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Annotated, Protocol, cast
from uuid import UUID

from fastapi import Depends, Request

from researchlens.modules.artifacts.application import (
    DownloadArtifactUseCase,
    GetArtifactDetailUseCase,
    ListRunArtifactsUseCase,
)
from researchlens.shared.errors import AuthenticationError
from researchlens.shared.logging import bind_tenant_id, reset_tenant_id


@dataclass(frozen=True, slots=True)
class RequestActor:
    tenant_id: UUID
    user_id: UUID


class AuthenticatedActor(Protocol):
    tenant_id: UUID
    user_id: UUID
    roles: list[str]


class AuthRuntime(Protocol):
    async def resolve_actor(self, *, access_token: str) -> AuthenticatedActor: ...


class ArtifactsRequestContext(Protocol):
    list_run_artifacts: ListRunArtifactsUseCase
    get_artifact_detail: GetArtifactDetailUseCase
    download_artifact: DownloadArtifactUseCase


class ArtifactsRuntime(Protocol):
    def request_context(self) -> AbstractAsyncContextManager[ArtifactsRequestContext]: ...


async def get_artifacts_context(request: Request) -> AsyncIterator[ArtifactsRequestContext]:
    runtime = cast(ArtifactsRuntime, request.app.state.bootstrap.artifacts_runtime)
    async with runtime.request_context() as context:
        yield context


async def get_request_actor(request: Request) -> AsyncIterator[RequestActor]:
    auth_runtime = cast(AuthRuntime, request.app.state.bootstrap.auth_runtime)
    actor_identity = await auth_runtime.resolve_actor(access_token=_extract_bearer_token(request))
    actor = RequestActor(tenant_id=actor_identity.tenant_id, user_id=actor_identity.user_id)
    token = bind_tenant_id(str(actor.tenant_id))
    try:
        yield actor
    finally:
        reset_tenant_id(token)


RequestActorDep = Annotated[RequestActor, Depends(get_request_actor)]
ArtifactsContext = Annotated[ArtifactsRequestContext, Depends(get_artifacts_context)]


def get_list_run_artifacts_use_case(context: ArtifactsContext) -> ListRunArtifactsUseCase:
    return context.list_run_artifacts


def get_artifact_detail_use_case(context: ArtifactsContext) -> GetArtifactDetailUseCase:
    return context.get_artifact_detail


def get_download_artifact_use_case(context: ArtifactsContext) -> DownloadArtifactUseCase:
    return context.download_artifact


def _extract_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise AuthenticationError("Bearer access token is required.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationError("Bearer access token is required.")
    return token
