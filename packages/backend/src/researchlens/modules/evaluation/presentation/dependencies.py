from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Annotated, Protocol, cast
from uuid import UUID

from fastapi import Depends, Request

from researchlens.modules.evaluation.application import (
    GetLatestEvaluationSummaryUseCase,
    ListEvaluationIssuesUseCase,
    LoadRepairCandidatesUseCase,
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


class EvaluationRequestContext(Protocol):
    get_latest_summary: GetLatestEvaluationSummaryUseCase
    list_issues: ListEvaluationIssuesUseCase
    load_repair_candidates: LoadRepairCandidatesUseCase


class EvaluationRuntime(Protocol):
    def request_context(self) -> AbstractAsyncContextManager[EvaluationRequestContext]: ...


async def get_evaluation_context(request: Request) -> AsyncIterator[EvaluationRequestContext]:
    runtime = cast(EvaluationRuntime, request.app.state.bootstrap.evaluation_runtime)
    async with runtime.request_context() as context:
        yield context


EvaluationContext = Annotated[EvaluationRequestContext, Depends(get_evaluation_context)]


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


RequestActorDep = Annotated[RequestActor, Depends(get_request_actor)]


def get_latest_summary_use_case(
    context: EvaluationContext,
) -> GetLatestEvaluationSummaryUseCase:
    return context.get_latest_summary


def get_list_issues_use_case(context: EvaluationContext) -> ListEvaluationIssuesUseCase:
    return context.list_issues


def _extract_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise AuthenticationError("Bearer access token is required.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationError("Bearer access token is required.")
    return token
