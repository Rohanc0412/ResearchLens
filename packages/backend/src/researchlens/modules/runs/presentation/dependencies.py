from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Annotated, Protocol, cast
from uuid import UUID

from fastapi import Depends, Request

from researchlens.modules.runs.application import (
    CancelRunUseCase,
    CreateRunUseCase,
    GetRunUseCase,
    ListRunEventsUseCase,
    RetryRunUseCase,
)
from researchlens.shared.errors import AuthenticationError
from researchlens.shared.logging import bind_tenant_id, reset_tenant_id


@dataclass(frozen=True, slots=True)
class RequestActor:
    tenant_id: UUID
    user_id: UUID


class RunsRequestContext(Protocol):
    create_run: CreateRunUseCase
    get_run: GetRunUseCase
    list_run_events: ListRunEventsUseCase
    cancel_run: CancelRunUseCase
    retry_run: RetryRunUseCase


class RunsRuntime(Protocol):
    def request_context(self) -> AbstractAsyncContextManager[RunsRequestContext]: ...


class AuthenticatedActor(Protocol):
    tenant_id: UUID
    user_id: UUID
    roles: list[str]


class AuthRuntime(Protocol):
    async def resolve_actor(self, *, access_token: str) -> AuthenticatedActor: ...


async def get_runs_context(request: Request) -> AsyncIterator[RunsRequestContext]:
    runtime = cast(RunsRuntime, request.app.state.bootstrap.runs_runtime)
    async with runtime.request_context() as context:
        yield context


async def get_request_actor(request: Request) -> AsyncIterator[RequestActor]:
    auth_runtime = cast(AuthRuntime, request.app.state.bootstrap.auth_runtime)
    actor_identity = await auth_runtime.resolve_actor(access_token=_extract_bearer_token(request))
    actor = RequestActor(
        tenant_id=actor_identity.tenant_id,
        user_id=actor_identity.user_id,
    )
    token = bind_tenant_id(str(actor.tenant_id))
    try:
        yield actor
    finally:
        reset_tenant_id(token)


RunsContext = Annotated[RunsRequestContext, Depends(get_runs_context)]


def _extract_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise AuthenticationError("Bearer access token is required.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationError("Bearer access token is required.")
    return token


def get_create_run_use_case(context: RunsContext) -> CreateRunUseCase:
    return context.create_run


def get_get_run_use_case(context: RunsContext) -> GetRunUseCase:
    return context.get_run


def get_list_run_events_use_case(context: RunsContext) -> ListRunEventsUseCase:
    return context.list_run_events


def get_cancel_run_use_case(context: RunsContext) -> CancelRunUseCase:
    return context.cancel_run


def get_retry_run_use_case(context: RunsContext) -> RetryRunUseCase:
    return context.retry_run
