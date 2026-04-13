from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from typing import Annotated, Protocol, cast
from uuid import UUID

from fastapi import Depends, Request

from researchlens.modules.evidence.application import (
    GetChunkDetailUseCase,
    GetRunEvidenceSummaryUseCase,
    GetSectionEvidenceTraceUseCase,
    GetSourceDetailUseCase,
)
from researchlens.shared.errors import AuthenticationError
from researchlens.shared.logging import bind_tenant_id, reset_tenant_id


class AuthenticatedActor(Protocol):
    tenant_id: UUID
    user_id: UUID
    roles: list[str]


class AuthRuntime(Protocol):
    async def resolve_actor(self, *, access_token: str) -> AuthenticatedActor: ...


class RequestActor(Protocol):
    tenant_id: UUID
    user_id: UUID


class EvidenceRequestContext(Protocol):
    get_run_summary: GetRunEvidenceSummaryUseCase
    get_section_trace: GetSectionEvidenceTraceUseCase
    get_chunk_detail: GetChunkDetailUseCase
    get_source_detail: GetSourceDetailUseCase


class EvidenceRuntime(Protocol):
    def request_context(self) -> AbstractAsyncContextManager[EvidenceRequestContext]: ...


async def get_evidence_context(request: Request) -> AsyncIterator[EvidenceRequestContext]:
    runtime = cast(EvidenceRuntime, request.app.state.bootstrap.evidence_runtime)
    async with runtime.request_context() as context:
        yield context


async def get_request_actor(request: Request) -> AsyncIterator[RequestActor]:
    auth_runtime = cast(AuthRuntime, request.app.state.bootstrap.auth_runtime)
    actor = await auth_runtime.resolve_actor(access_token=_extract_bearer_token(request))
    token = bind_tenant_id(str(actor.tenant_id))
    try:
        yield actor
    finally:
        reset_tenant_id(token)


RequestActorDep = Annotated[RequestActor, Depends(get_request_actor)]
EvidenceContext = Annotated[EvidenceRequestContext, Depends(get_evidence_context)]


def get_run_summary_use_case(context: EvidenceContext) -> GetRunEvidenceSummaryUseCase:
    return context.get_run_summary


def get_section_trace_use_case(context: EvidenceContext) -> GetSectionEvidenceTraceUseCase:
    return context.get_section_trace


def get_chunk_detail_use_case(context: EvidenceContext) -> GetChunkDetailUseCase:
    return context.get_chunk_detail


def get_source_detail_use_case(context: EvidenceContext) -> GetSourceDetailUseCase:
    return context.get_source_detail


def _extract_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise AuthenticationError("Bearer access token is required.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationError("Bearer access token is required.")
    return token
