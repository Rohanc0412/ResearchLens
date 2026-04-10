from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from researchlens.modules.conversations.application import (
    CreateConversationCommand,
    CreateConversationUseCase,
    DeleteConversationCommand,
    DeleteConversationUseCase,
    GetConversationQuery,
    GetConversationUseCase,
    ListConversationsQuery,
    ListConversationsUseCase,
    UpdateConversationCommand,
    UpdateConversationUseCase,
)
from researchlens.modules.conversations.presentation.dependencies import (
    RequestActor,
    get_create_conversation_use_case,
    get_delete_conversation_use_case,
    get_get_conversation_use_case,
    get_list_conversations_use_case,
    get_request_actor,
    get_update_conversation_use_case,
)
from researchlens.modules.conversations.presentation.schemas import (
    ConversationListResponse,
    ConversationResponse,
    CreateConversationRequest,
    UpdateConversationRequest,
)

router = APIRouter(tags=["conversations"])
RequestActorDep = Annotated[RequestActor, Depends(get_request_actor)]
CreateConversationUseCaseDep = Annotated[
    CreateConversationUseCase,
    Depends(get_create_conversation_use_case),
]
ListConversationsUseCaseDep = Annotated[
    ListConversationsUseCase,
    Depends(get_list_conversations_use_case),
]
GetConversationUseCaseDep = Annotated[
    GetConversationUseCase,
    Depends(get_get_conversation_use_case),
]
UpdateConversationUseCaseDep = Annotated[
    UpdateConversationUseCase,
    Depends(get_update_conversation_use_case),
]
DeleteConversationUseCaseDep = Annotated[
    DeleteConversationUseCase,
    Depends(get_delete_conversation_use_case),
]


@router.post(
    "/projects/{project_id}/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    project_id: UUID,
    payload: CreateConversationRequest,
    actor: RequestActorDep,
    use_case: CreateConversationUseCaseDep,
) -> ConversationResponse:
    conversation = await use_case.execute(
        CreateConversationCommand(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            project_id=project_id,
            title=payload.title,
        )
    )
    return ConversationResponse.model_validate(conversation)


@router.get(
    "/projects/{project_id}/conversations",
    response_model=ConversationListResponse,
)
async def list_conversations(
    project_id: UUID,
    actor: RequestActorDep,
    use_case: ListConversationsUseCaseDep,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20),
) -> ConversationListResponse:
    page = await use_case.execute(
        ListConversationsQuery(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            project_id=project_id,
            cursor=cursor,
            limit=limit,
        )
    )
    return ConversationListResponse(
        items=[ConversationResponse.model_validate(item) for item in page.items],
        next_cursor=page.next_cursor,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    actor: RequestActorDep,
    use_case: GetConversationUseCaseDep,
) -> ConversationResponse:
    conversation = await use_case.execute(
        GetConversationQuery(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            conversation_id=conversation_id,
        )
    )
    return ConversationResponse.model_validate(conversation)


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    payload: UpdateConversationRequest,
    actor: RequestActorDep,
    use_case: UpdateConversationUseCaseDep,
) -> ConversationResponse:
    conversation = await use_case.execute(
        UpdateConversationCommand(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            conversation_id=conversation_id,
            title=payload.title,
        )
    )
    return ConversationResponse.model_validate(conversation)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    actor: RequestActorDep,
    use_case: DeleteConversationUseCaseDep,
) -> Response:
    await use_case.execute(
        DeleteConversationCommand(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            conversation_id=conversation_id,
        )
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
