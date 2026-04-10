from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Annotated, Protocol, cast
from uuid import UUID

from fastapi import Depends, Request

from researchlens.modules.conversations.application import (
    CreateConversationUseCase,
    DeleteConversationUseCase,
    GetConversationUseCase,
    GetMessageUseCase,
    ListConversationsUseCase,
    ListMessagesUseCase,
    PostMessageUseCase,
    RecordRunTriggerUseCase,
    UpdateConversationUseCase,
)
from researchlens.shared.errors import AuthenticationError
from researchlens.shared.logging import bind_tenant_id, reset_tenant_id


@dataclass(frozen=True, slots=True)
class RequestActor:
    tenant_id: UUID
    user_id: UUID


class ConversationsRequestContext(Protocol):
    create_conversation: CreateConversationUseCase
    list_conversations: ListConversationsUseCase
    get_conversation: GetConversationUseCase
    update_conversation: UpdateConversationUseCase
    delete_conversation: DeleteConversationUseCase
    post_message: PostMessageUseCase
    list_messages: ListMessagesUseCase
    get_message: GetMessageUseCase
    record_run_trigger: RecordRunTriggerUseCase


class ConversationsRuntime(Protocol):
    def request_context(self) -> AbstractAsyncContextManager[ConversationsRequestContext]: ...


class AuthenticatedActor(Protocol):
    tenant_id: UUID
    user_id: UUID
    roles: list[str]


class AuthRuntime(Protocol):
    async def resolve_actor(self, *, access_token: str) -> AuthenticatedActor: ...


async def get_conversations_context(
    request: Request,
) -> AsyncIterator[ConversationsRequestContext]:
    runtime = cast(ConversationsRuntime, request.app.state.bootstrap.conversations_runtime)
    async with runtime.request_context() as context:
        yield context


async def get_request_actor(request: Request) -> AsyncIterator[RequestActor]:
    auth_runtime = cast(AuthRuntime, request.app.state.bootstrap.auth_runtime)
    actor_identity = await auth_runtime.resolve_actor(
        access_token=_extract_bearer_token(request),
    )
    actor = RequestActor(
        tenant_id=actor_identity.tenant_id,
        user_id=actor_identity.user_id,
    )
    token = bind_tenant_id(str(actor.tenant_id))
    try:
        yield actor
    finally:
        reset_tenant_id(token)


ConversationsContext = Annotated[
    ConversationsRequestContext,
    Depends(get_conversations_context),
]


def _extract_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise AuthenticationError("Bearer access token is required.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationError("Bearer access token is required.")
    return token


def get_create_conversation_use_case(
    context: ConversationsContext,
) -> CreateConversationUseCase:
    return context.create_conversation


def get_list_conversations_use_case(
    context: ConversationsContext,
) -> ListConversationsUseCase:
    return context.list_conversations


def get_get_conversation_use_case(
    context: ConversationsContext,
) -> GetConversationUseCase:
    return context.get_conversation


def get_update_conversation_use_case(
    context: ConversationsContext,
) -> UpdateConversationUseCase:
    return context.update_conversation


def get_delete_conversation_use_case(
    context: ConversationsContext,
) -> DeleteConversationUseCase:
    return context.delete_conversation


def get_post_message_use_case(context: ConversationsContext) -> PostMessageUseCase:
    return context.post_message


def get_list_messages_use_case(context: ConversationsContext) -> ListMessagesUseCase:
    return context.list_messages


def get_get_message_use_case(context: ConversationsContext) -> GetMessageUseCase:
    return context.get_message


def get_record_run_trigger_use_case(
    context: ConversationsContext,
) -> RecordRunTriggerUseCase:
    return context.record_run_trigger
