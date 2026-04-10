from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from researchlens.modules.conversations.application import (
    GetMessageQuery,
    GetMessageUseCase,
    ListMessagesQuery,
    ListMessagesUseCase,
    PostMessageCommand,
    PostMessageUseCase,
)
from researchlens.modules.conversations.domain import MessageRole, MessageType
from researchlens.modules.conversations.presentation.dependencies import (
    RequestActor,
    get_get_message_use_case,
    get_list_messages_use_case,
    get_post_message_use_case,
    get_request_actor,
)
from researchlens.modules.conversations.presentation.schemas import (
    MessageResponse,
    MessageWriteResponse,
    PostMessageRequest,
)

router = APIRouter(tags=["messages"])
RequestActorDep = Annotated[RequestActor, Depends(get_request_actor)]
PostMessageUseCaseDep = Annotated[PostMessageUseCase, Depends(get_post_message_use_case)]
ListMessagesUseCaseDep = Annotated[ListMessagesUseCase, Depends(get_list_messages_use_case)]
GetMessageUseCaseDep = Annotated[GetMessageUseCase, Depends(get_get_message_use_case)]


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageWriteResponse,
)
async def post_message(
    conversation_id: UUID,
    payload: PostMessageRequest,
    actor: RequestActorDep,
    response: Response,
    use_case: PostMessageUseCaseDep,
) -> MessageWriteResponse:
    result = await use_case.execute(
        PostMessageCommand(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            conversation_id=conversation_id,
            role=MessageRole(payload.role),
            type=MessageType(payload.type),
            content_text=payload.content_text,
            content_json=payload.content_json,
            metadata_json=payload.metadata_json,
            client_message_id=payload.client_message_id,
        )
    )
    response.status_code = (
        status.HTTP_200_OK if result.idempotent_replay else status.HTTP_201_CREATED
    )
    return MessageWriteResponse.model_validate(
        {**asdict(result.message), "idempotent_replay": result.idempotent_replay}
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: UUID,
    actor: RequestActorDep,
    use_case: ListMessagesUseCaseDep,
) -> list[MessageResponse]:
    messages = await use_case.execute(
        ListMessagesQuery(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            conversation_id=conversation_id,
        )
    )
    return [MessageResponse.model_validate(message) for message in messages]


@router.get(
    "/conversations/{conversation_id}/messages/{message_id}",
    response_model=MessageResponse,
)
async def get_message(
    conversation_id: UUID,
    message_id: UUID,
    actor: RequestActorDep,
    use_case: GetMessageUseCaseDep,
) -> MessageResponse:
    message = await use_case.execute(
        GetMessageQuery(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            conversation_id=conversation_id,
            message_id=message_id,
        )
    )
    return MessageResponse.model_validate(message)
