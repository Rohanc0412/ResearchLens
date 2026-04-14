from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from fastapi.responses import StreamingResponse

from researchlens.modules.runs.application import (
    CancelRunCommand,
    CancelRunUseCase,
    CreateRunCommand,
    CreateRunUseCase,
    GetRunQuery,
    ListRunEventsQuery,
    RetryRunCommand,
    RetryRunUseCase,
)
from researchlens.modules.runs.presentation.dependencies import (
    RequestActor,
    RunsRuntime,
    get_cancel_run_use_case,
    get_create_run_use_case,
    get_request_actor,
    get_retry_run_use_case,
)
from researchlens.modules.runs.presentation.run_request_models import CreateRunRequest
from researchlens.modules.runs.presentation.run_response_models import (
    CreateRunResponse,
    RunEventResponse,
    RunSummaryResponse,
)
from researchlens.modules.runs.presentation.run_sse import stream_run_events

router = APIRouter(tags=["runs"])
RequestActorDep = Annotated[RequestActor, Depends(get_request_actor)]
CreateRunUseCaseDep = Annotated[CreateRunUseCase, Depends(get_create_run_use_case)]
CancelRunUseCaseDep = Annotated[CancelRunUseCase, Depends(get_cancel_run_use_case)]
RetryRunUseCaseDep = Annotated[RetryRunUseCase, Depends(get_retry_run_use_case)]


@router.post(
    "/conversations/{conversation_id}/runs",
    response_model=CreateRunResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/conversations/{conversation_id}/run-triggers",
    response_model=CreateRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_run(
    response: Response,
    conversation_id: UUID,
    payload: CreateRunRequest,
    actor: RequestActorDep,
    use_case: CreateRunUseCaseDep,
) -> CreateRunResponse:
    result = await use_case.execute(
        CreateRunCommand(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            conversation_id=conversation_id,
            source_message_id=payload.source_message_id,
            request_text=payload.request_text,
            client_request_id=payload.client_request_id,
            output_type=payload.output_type,
        )
    )
    if result.idempotent_replay:
        response.status_code = status.HTTP_200_OK
    return CreateRunResponse.model_validate(result)


@router.get("/runs/{run_id}", response_model=RunSummaryResponse)
async def get_run(
    request: Request,
    run_id: UUID,
    actor: RequestActorDep,
) -> RunSummaryResponse:
    runtime = cast(RunsRuntime, request.app.state.bootstrap.runs_runtime)
    async with runtime.request_context() as context:
        run = await context.get_run.execute(GetRunQuery(tenant_id=actor.tenant_id, run_id=run_id))
    return RunSummaryResponse.model_validate(run)


@router.get("/runs/{run_id}/events", response_model=list[RunEventResponse])
async def list_or_stream_run_events(
    request: Request,
    run_id: UUID,
    actor: RequestActorDep,
    after_event_number: int | None = Query(default=None, ge=0),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
) -> StreamingResponse | list[RunEventResponse]:
    runtime = cast(RunsRuntime, request.app.state.bootstrap.runs_runtime)
    if "text/event-stream" in request.headers.get("accept", ""):
        settings = request.app.state.bootstrap.settings.queue
        stream = stream_run_events(
            tenant_id=actor.tenant_id,
            run_id=run_id,
            last_event_id=int(last_event_id) if last_event_id else None,
            request_context_factory=runtime.request_context,
            keepalive_seconds=settings.sse_keepalive_seconds,
            terminal_grace_seconds=settings.sse_terminal_grace_seconds,
        )
        return StreamingResponse(stream, media_type="text/event-stream")

    async with runtime.request_context() as context:
        events = await context.list_run_events.execute(
            ListRunEventsQuery(
                tenant_id=actor.tenant_id,
                run_id=run_id,
                after_event_number=after_event_number,
            )
        )
    return [RunEventResponse.model_validate(event) for event in events]


@router.post("/runs/{run_id}/cancel", response_model=RunSummaryResponse)
async def cancel_run(
    run_id: UUID,
    actor: RequestActorDep,
    use_case: CancelRunUseCaseDep,
) -> RunSummaryResponse:
    run = await use_case.execute(CancelRunCommand(tenant_id=actor.tenant_id, run_id=run_id))
    return RunSummaryResponse.model_validate(run)


@router.post("/runs/{run_id}/retry", response_model=RunSummaryResponse)
async def retry_run(
    run_id: UUID,
    actor: RequestActorDep,
    use_case: RetryRunUseCaseDep,
) -> RunSummaryResponse:
    run = await use_case.execute(RetryRunCommand(tenant_id=actor.tenant_id, run_id=run_id))
    return RunSummaryResponse.model_validate(run)
