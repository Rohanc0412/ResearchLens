from datetime import UTC, datetime, timedelta

import pytest
from packages.backend.tests.integration.run_worker_lifecycle_support import (
    ControlledStageExecution,
    WorkerCrash,
    cancel_run,
    claim_one,
    create_run,
    get_run,
    list_run_events,
    mark_run_running,
    process_claimed,
    retry_run,
    seed_project_conversation,
)
from sqlalchemy import func, select

from researchlens.modules.retrieval.infrastructure.persistence.rows import RunRetrievalSourceRow
from researchlens.modules.runs.domain import RunStage
from researchlens.shared.config import get_settings
from researchlens.shared.db import DatabaseRuntime
from researchlens.worker_composition import build_worker_runs_runtime, poll_worker_once


@pytest.mark.asyncio
async def test_queue_lease_is_exclusive_and_expired_lease_can_be_reclaimed(
    database_runtime: DatabaseRuntime,
) -> None:
    tenant_id, user_id, conversation_id = await seed_project_conversation(database_runtime)
    run_id = await create_run(
        database_runtime,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    claimed_one = await claim_one(database_runtime, now=datetime.now(tz=UTC))
    claimed_two = await claim_one(database_runtime, now=datetime.now(tz=UTC))
    reclaimed = await claim_one(database_runtime, now=datetime.now(tz=UTC) + timedelta(seconds=31))

    assert claimed_one is not None
    assert claimed_one.run_id == run_id
    assert claimed_two is None
    assert reclaimed is not None
    assert reclaimed.run_id == run_id


@pytest.mark.asyncio
async def test_retry_before_drafting_uses_latest_successful_checkpoint(
    database_runtime: DatabaseRuntime,
) -> None:
    tenant_id, user_id, conversation_id = await seed_project_conversation(database_runtime)
    run_id = await create_run(
        database_runtime,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    claimed = await claim_one(database_runtime, now=datetime.now(tz=UTC))
    assert claimed is not None

    await process_claimed(
        database_runtime,
        claimed=claimed,
        stage_execution=ControlledStageExecution(fail_before_stage=RunStage.DRAFT),
    )
    retried = await retry_run(database_runtime, tenant_id=tenant_id, run_id=run_id)

    assert retried.status == "queued"
    assert retried.current_stage == "retrieve"
    assert retried.retry_count == 1


@pytest.mark.asyncio
async def test_retry_after_drafting_restarts_from_draft(
    database_runtime: DatabaseRuntime,
) -> None:
    tenant_id, user_id, conversation_id = await seed_project_conversation(database_runtime)
    run_id = await create_run(
        database_runtime,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    claimed = await claim_one(database_runtime, now=datetime.now(tz=UTC))
    assert claimed is not None

    await process_claimed(
        database_runtime,
        claimed=claimed,
        stage_execution=ControlledStageExecution(fail_before_stage=RunStage.EVALUATE),
    )
    retried = await retry_run(database_runtime, tenant_id=tenant_id, run_id=run_id)

    assert retried.status == "queued"
    assert retried.current_stage == "draft"
    assert retried.retry_count == 1


@pytest.mark.asyncio
async def test_worker_restart_resumes_from_checkpoint_without_duplicate_stage_completion(
    database_runtime: DatabaseRuntime,
) -> None:
    tenant_id, user_id, conversation_id = await seed_project_conversation(database_runtime)
    run_id = await create_run(
        database_runtime,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    claimed = await claim_one(database_runtime, now=datetime.now(tz=UTC))
    assert claimed is not None

    with pytest.raises(WorkerCrash):
        await process_claimed(
            database_runtime,
            claimed=claimed,
            stage_execution=ControlledStageExecution(crash_after_stage=RunStage.RETRIEVE),
        )

    reclaimed = await claim_one(database_runtime, now=datetime.now(tz=UTC) + timedelta(seconds=31))
    assert reclaimed is not None
    await process_claimed(
        database_runtime,
        claimed=reclaimed,
        stage_execution=ControlledStageExecution(),
    )
    events = await list_run_events(database_runtime, tenant_id=tenant_id, run_id=run_id)
    run = await get_run(database_runtime, tenant_id=tenant_id, run_id=run_id)

    retrieve_completions = [
        event
        for event in events
        if event.event_type == "stage.completed" and event.stage == "retrieve"
    ]
    assert len(retrieve_completions) == 1
    assert run.status == "succeeded"


@pytest.mark.asyncio
async def test_running_cancel_requests_stop_and_worker_finishes_cleanly(
    database_runtime: DatabaseRuntime,
) -> None:
    tenant_id, user_id, conversation_id = await seed_project_conversation(database_runtime)
    run_id = await create_run(
        database_runtime,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    claimed = await claim_one(database_runtime, now=datetime.now(tz=UTC))
    assert claimed is not None

    await mark_run_running(database_runtime, run_id=run_id)
    await cancel_run(database_runtime, tenant_id=tenant_id, run_id=run_id)
    await process_claimed(
        database_runtime,
        claimed=claimed,
        stage_execution=ControlledStageExecution(),
    )
    run = await get_run(database_runtime, tenant_id=tenant_id, run_id=run_id)
    events = await list_run_events(database_runtime, tenant_id=tenant_id, run_id=run_id)

    assert run.status == "canceled"
    assert any(event.event_type == "cancel.requested" for event in events)
    assert any(event.event_type == "run.canceled" for event in events)


@pytest.mark.asyncio
async def test_worker_composition_runs_retrieval_stage_and_persists_sources(
    database_runtime: DatabaseRuntime,
) -> None:
    tenant_id, user_id, conversation_id = await seed_project_conversation(database_runtime)
    run_id = await create_run(
        database_runtime,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    settings = get_settings()
    runs_runtime = build_worker_runs_runtime(database=database_runtime, settings=settings)

    await poll_worker_once(runs_runtime=runs_runtime, settings=settings)

    events = await list_run_events(database_runtime, tenant_id=tenant_id, run_id=run_id)
    async with database_runtime.session_factory() as session:
        linked_count = await session.scalar(
            select(func.count()).select_from(RunRetrievalSourceRow).where(
                RunRetrievalSourceRow.run_id == run_id
            )
        )

    assert linked_count is not None
    assert 0 < linked_count <= settings.retrieval.max_selected_sources
    assert any(event.message == "Retrieval summary completed" for event in events)
