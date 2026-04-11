from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from researchlens.modules.conversations.infrastructure.rows.conversation_row import ConversationRow
from researchlens.modules.projects.infrastructure.project_row import ProjectRow
from researchlens.modules.retrieval.infrastructure.persistence.rows import RunRetrievalSourceRow
from researchlens.modules.runs.application import CreateRunCommand, CreateRunUseCase
from researchlens.modules.runs.infrastructure.conversation_scope_reader_sql import (
    SqlAlchemyConversationScopeReader,
)
from researchlens.modules.runs.infrastructure.message_scope_reader_sql import (
    SqlAlchemyMessageScopeReader,
)
from researchlens.modules.runs.infrastructure.queue_backend_db import DbRunQueueBackend
from researchlens.modules.runs.infrastructure.run_event_store_sql import SqlAlchemyRunEventStore
from researchlens.modules.runs.infrastructure.run_repository_sql import SqlAlchemyRunRepository
from researchlens.shared.config import get_settings
from researchlens.shared.db import DatabaseRuntime, SqlAlchemyTransactionManager
from researchlens.worker_composition import build_worker_runs_runtime, poll_worker_once


@pytest.mark.asyncio
async def test_phase6_retrieval_runs_from_conversation_to_persisted_sources(
    database_runtime: DatabaseRuntime,
) -> None:
    tenant_id, user_id, conversation_id = await _seed_conversation(database_runtime)
    run_id = await _create_conversation_run(
        database_runtime,
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    settings = get_settings()
    runs_runtime = build_worker_runs_runtime(database=database_runtime, settings=settings)

    await poll_worker_once(runs_runtime=runs_runtime, settings=settings)

    async with database_runtime.session_factory() as session:
        linked_count = await session.scalar(
            select(func.count()).select_from(RunRetrievalSourceRow).where(
                RunRetrievalSourceRow.run_id == run_id
            )
        )

    assert linked_count is not None
    assert linked_count > 0


async def _seed_conversation(
    database_runtime: DatabaseRuntime,
) -> tuple[UUID, UUID, UUID]:
    tenant_id = uuid4()
    user_id = uuid4()
    project_id = uuid4()
    conversation_id = uuid4()
    now = datetime.now(tz=UTC)
    async with database_runtime.session_factory() as session:
        session.add(
            ProjectRow(
                id=project_id,
                tenant_id=tenant_id,
                name="Alpha",
                description=None,
                created_by=str(user_id),
                created_at=now,
                updated_at=now,
            )
        )
        session.add(
            ConversationRow(
                id=conversation_id,
                tenant_id=tenant_id,
                project_id=project_id,
                created_by_user_id=user_id,
                title="Thread",
                created_at=now,
                updated_at=now,
                last_message_at=None,
            )
        )
        await session.commit()
    return tenant_id, user_id, conversation_id


async def _create_conversation_run(
    database_runtime: DatabaseRuntime,
    *,
    tenant_id: UUID,
    user_id: UUID,
    conversation_id: UUID,
) -> UUID:
    async with database_runtime.session_factory() as session:
        result = await CreateRunUseCase(
            conversation_scope_reader=SqlAlchemyConversationScopeReader(session),
            message_scope_reader=SqlAlchemyMessageScopeReader(session),
            run_repository=SqlAlchemyRunRepository(session),
            event_store=SqlAlchemyRunEventStore(session),
            queue_backend=DbRunQueueBackend(session),
            transaction_manager=SqlAlchemyTransactionManager(session),
        ).execute(
            CreateRunCommand(
                tenant_id=tenant_id,
                user_id=user_id,
                conversation_id=conversation_id,
                source_message_id=None,
                request_text="Retrieve sources about AI safety benchmarks",
                client_request_id=None,
                output_type="report",
            )
        )
        return result.run.id
