"""Chat send endpoint: processes user messages and returns either a JSON response
or an SSE stream (for quick-answer paths that call the LLM)."""
from __future__ import annotations

import json
import logging
from dataclasses import asdict
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from researchlens.modules.conversations.application import (
    ChatSendImmediateResult,
    ChatSendStreamContext,
    SendChatMessageCommand,
    SendChatMessageUseCase,
)
from researchlens.modules.conversations.infrastructure.quick_answer_streamer import (
    QuickAnswerStreamer,
    _message_view_to_dict,
)
from researchlens.modules.conversations.infrastructure.runtime import (
    SqlAlchemyConversationsRuntime,
)
from researchlens.modules.conversations.presentation.dependencies import (
    RequestActor,
    get_request_actor,
)
from researchlens.modules.conversations.presentation.schemas import (
    ChatSendRequest,
    ChatSendResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])
RequestActorDep = Annotated[RequestActor, Depends(get_request_actor)]


def _get_send_use_case(request: Request) -> SendChatMessageUseCase:
    runtime = cast(
        SqlAlchemyConversationsRuntime,
        request.app.state.bootstrap.conversations_runtime,
    )

    async def _factory() -> SendChatMessageUseCase:
        async with runtime.request_context() as ctx:
            yield ctx.send_chat_message

    return Depends(_factory)


def _get_streamer(request: Request) -> QuickAnswerStreamer:
    runtime = cast(
        SqlAlchemyConversationsRuntime,
        request.app.state.bootstrap.conversations_runtime,
    )
    return runtime.quick_answer_streamer()


@router.post("/conversations/{conversation_id}/send")
async def send_chat_message(
    conversation_id: UUID,
    payload: ChatSendRequest,
    actor: RequestActorDep,
    request: Request,
) -> Any:
    runtime = cast(
        SqlAlchemyConversationsRuntime,
        request.app.state.bootstrap.conversations_runtime,
    )

    command = SendChatMessageCommand(
        tenant_id=actor.tenant_id,
        user_id=actor.user_id,
        conversation_id=conversation_id,
        message=payload.message,
        client_message_id=payload.client_message_id,
        llm_model=payload.llm_model,
        force_pipeline=payload.force_pipeline,
    )

    async with runtime.request_context() as ctx:
        result = await ctx.send_chat_message.execute(command)

    if isinstance(result, ChatSendImmediateResult):
        return _to_json_response(conversation_id, result)

    # Streaming path: commit already happened inside the use case transaction.
    streamer = runtime.quick_answer_streamer()
    return StreamingResponse(
        streamer.stream_with_status(result),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _to_json_response(
    conversation_id: UUID,
    result: ChatSendImmediateResult,
) -> ChatSendResponse:
    return ChatSendResponse(
        conversation_id=conversation_id,
        user_message=_view_to_schema(result.user_message),
        assistant_message=_view_to_schema(result.assistant_message),
        pending_action=result.pending_action,
        idempotent_replay=result.idempotent_replay,
    )


def _view_to_schema(view: Any) -> Any:
    if view is None:
        return None
    from researchlens.modules.conversations.presentation.schemas import ChatMessageView
    return ChatMessageView(
        id=view.id,
        role=view.role,
        type=view.type,
        content_text=view.content_text,
        content_json=view.content_json,
        created_at=view.created_at,
        client_message_id=view.client_message_id,
    )
