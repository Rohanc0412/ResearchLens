from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from typing import Annotated, Protocol, cast
from uuid import UUID

from fastapi import Depends, Request

from researchlens.modules.repair.application import GetLatestRepairSummaryUseCase
from researchlens.shared.errors import AuthenticationError
from researchlens.shared.logging import bind_tenant_id, reset_tenant_id


class RequestActor(Protocol):
    tenant_id: UUID
    user_id: UUID


class AuthenticatedActor(Protocol):
    tenant_id: UUID
    user_id: UUID
    roles: list[str]


class AuthRuntime(Protocol):
    async def resolve_actor(self, *, access_token: str) -> AuthenticatedActor: ...


class RepairRequestContext(Protocol):
    get_latest_summary: GetLatestRepairSummaryUseCase


class RepairRuntime(Protocol):
    def request_context(self) -> AbstractAsyncContextManager[RepairRequestContext]: ...


async def get_repair_context(request: Request) -> AsyncIterator[RepairRequestContext]:
    runtime = cast(RepairRuntime, request.app.state.bootstrap.repair_runtime)
    async with runtime.request_context() as context:
        yield context


RepairContext = Annotated[RepairRequestContext, Depends(get_repair_context)]


async def get_request_actor(request: Request) -> AsyncIterator[AuthenticatedActor]:
    auth_runtime = cast(AuthRuntime, request.app.state.bootstrap.auth_runtime)
    actor = await auth_runtime.resolve_actor(access_token=_extract_bearer_token(request))
    token = bind_tenant_id(str(actor.tenant_id))
    try:
        yield actor
    finally:
        reset_tenant_id(token)


RequestActorDep = Annotated[AuthenticatedActor, Depends(get_request_actor)]


def get_latest_summary_use_case(context: RepairContext) -> GetLatestRepairSummaryUseCase:
    return context.get_latest_summary


LatestRepairSummaryDep = Annotated[
    GetLatestRepairSummaryUseCase,
    Depends(get_latest_summary_use_case),
]


def _extract_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise AuthenticationError("Bearer access token is required.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationError("Bearer access token is required.")
    return token
