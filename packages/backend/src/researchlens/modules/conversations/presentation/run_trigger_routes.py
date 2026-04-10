from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from researchlens.modules.conversations.application import (
    RecordRunTriggerCommand,
    RecordRunTriggerUseCase,
)
from researchlens.modules.conversations.presentation.dependencies import (
    RequestActor,
    get_record_run_trigger_use_case,
    get_request_actor,
)
from researchlens.modules.conversations.presentation.schemas import (
    RecordRunTriggerRequest,
    RunTriggerResponse,
)

router = APIRouter(tags=["run-triggers"])
RequestActorDep = Annotated[RequestActor, Depends(get_request_actor)]
RecordRunTriggerUseCaseDep = Annotated[
    RecordRunTriggerUseCase,
    Depends(get_record_run_trigger_use_case),
]


@router.post(
    "/conversations/{conversation_id}/run-triggers",
    response_model=RunTriggerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_run_trigger(
    conversation_id: UUID,
    payload: RecordRunTriggerRequest,
    actor: RequestActorDep,
    use_case: RecordRunTriggerUseCaseDep,
) -> RunTriggerResponse:
    trigger = await use_case.execute(
        RecordRunTriggerCommand(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            conversation_id=conversation_id,
            source_message_id=payload.source_message_id,
            request_text=payload.request_text,
            client_request_id=payload.client_request_id,
        )
    )
    return RunTriggerResponse.model_validate(trigger)
