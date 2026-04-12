import asyncio
import re
from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.conversations.infrastructure.rows.conversation_row import ConversationRow
from researchlens.modules.projects.infrastructure.project_row import ProjectRow
from researchlens.modules.retrieval.infrastructure.persistence.rows import (
    RetrievalSourceChunkRow,
    RetrievalSourceRow,
    RetrievalSourceSnapshotRow,
    RunRetrievalSourceRow,
)
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
from researchlens.shared.db import SqlAlchemyTransactionManager
from researchlens.shared.llm.domain import StructuredGenerationRequest, StructuredGenerationResult


class FakeDraftingClient:
    def __init__(
        self,
        *,
        fail_empty: bool = False,
        malformed_once_for: set[str] | None = None,
        invalid_once_for: set[str] | None = None,
        wait_event: asyncio.Event | None = None,
        release_event: asyncio.Event | None = None,
    ) -> None:
        self._fail_empty = fail_empty
        self._malformed_once_for = malformed_once_for or set()
        self._invalid_once_for = invalid_once_for or set()
        self._attempts: dict[str, int] = defaultdict(int)
        self._wait_event = wait_event
        self._release_event = release_event
        self.max_active_calls = 0
        self._active_calls = 0

    @property
    def model(self) -> str:
        return "gpt-5-nano"

    async def generate_structured(
        self,
        request: StructuredGenerationRequest,
    ) -> StructuredGenerationResult:
        section_id = _extract(r"Section id: ([^\n]+)", request.prompt)
        chunk_id = _extract(r"\[\[chunk:([0-9a-fA-F-]+)\]\]", _evidence_tokens(request.prompt))
        self._attempts[section_id] += 1
        self._active_calls += 1
        self.max_active_calls = max(self.max_active_calls, self._active_calls)
        try:
            if self._wait_event is not None and self._release_event is not None:
                self._wait_event.set()
                await self._release_event.wait()
            if self._fail_empty:
                return StructuredGenerationResult(data={})
            if section_id in self._malformed_once_for and self._attempts[section_id] == 1:
                return StructuredGenerationResult(data={"section_id": section_id})
            if section_id in self._invalid_once_for and self._attempts[section_id] == 1:
                return StructuredGenerationResult(
                    data={
                        "section_id": section_id,
                        "section_text": (
                            "Unsupported claim "
                            "[[chunk:00000000-0000-0000-0000-000000000000]]"
                        ),
                        "section_summary": "Bridge only.",
                        "status": "completed",
                    }
                )
            return StructuredGenerationResult(
                data={
                    "section_id": section_id,
                    "section_text": f"{section_id} grounded statement [[chunk:{chunk_id}]]",
                    "section_summary": f"{section_id} bridge.",
                    "status": "completed",
                }
            )
        finally:
            self._active_calls -= 1


async def seed_run_with_retrieval_outputs(
    session: AsyncSession,
    *,
    section_ids: tuple[str, ...],
) -> tuple[UUID, UUID]:
    tenant_id = uuid4()
    user_id = uuid4()
    project_id = uuid4()
    conversation_id = uuid4()
    now = datetime.now(tz=UTC)
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
    await session.flush()
    run = await CreateRunUseCase(
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
            request_text="What is the state of AI safety benchmarking?",
            client_request_id=None,
            output_type="report",
        )
    )
    for rank, section_id in enumerate(section_ids, start=1):
        await _insert_source_bundle(
            session,
            run_id=run.run.id,
            tenant_id=tenant_id,
            rank=rank,
            section_id=section_id,
        )
    await session.commit()
    return tenant_id, run.run.id


async def _insert_source_bundle(
    session: AsyncSession,
    *,
    run_id: UUID,
    tenant_id: UUID,
    rank: int,
    section_id: str,
) -> None:
    now = datetime.now(tz=UTC)
    source_id = uuid4()
    snapshot_id = uuid4()
    chunk_id = uuid4()
    session.add(
        RetrievalSourceRow(
            id=source_id,
            canonical_key=f"{section_id}-{rank}",
            provider_name="paper_search_mcp",
            provider_record_id=f"{section_id}-{rank}",
            title=f"{section_id.title()} source",
            identifiers_json={"url": f"https://example.test/{section_id}/{rank}"},
            metadata_json={},
            created_at=now,
            updated_at=now,
        )
    )
    session.add(
        RetrievalSourceSnapshotRow(
            id=snapshot_id,
            source_id=source_id,
            content_hash=f"{section_id}-{rank}",
            content_kind="abstract",
            content_text=f"{section_id} source body",
            created_at=now,
        )
    )
    session.add(
        RetrievalSourceChunkRow(
            id=chunk_id,
            snapshot_id=snapshot_id,
            chunk_index=0,
            text_hash=f"{section_id}-{rank}-chunk",
            text=f"{section_id} evidence chunk text",
            created_at=now,
        )
    )
    session.add(
        RunRetrievalSourceRow(
            id=uuid4(),
            run_id=run_id,
            source_id=source_id,
            target_section=section_id,
            query_intent=section_id,
            rank=rank,
            score=1.0 / rank,
            created_at=now,
        )
    )


def _extract(pattern: str, text: str) -> str:
    match = re.search(pattern, text)
    assert match is not None
    return match.group(1).strip()


def _evidence_tokens(prompt: str) -> str:
    return re.sub(r"chunk=([0-9a-fA-F-]+)", r"[[chunk:\1]]", prompt)
