from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from researchlens.modules.runs.domain import (
    Run,
    RunCheckpointRecord,
    RunEventAudience,
    RunEventLevel,
    RunEventRecord,
    RunEventType,
    RunQueueItem,
    RunStage,
    RunTransitionRecord,
)


@dataclass(frozen=True, slots=True)
class ConversationRunSource:
    conversation_id: UUID
    project_id: UUID


class ConversationScopeReader(Protocol):
    async def get_conversation_source(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
    ) -> ConversationRunSource | None: ...


class MessageScopeReader(Protocol):
    async def message_exists_for_conversation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
    ) -> bool: ...


class RunRepository(Protocol):
    async def add(self, run: Run) -> Run: ...

    async def get_by_id_for_tenant(self, *, tenant_id: UUID, run_id: UUID) -> Run | None: ...

    async def get_by_id(self, *, run_id: UUID) -> Run | None: ...

    async def get_by_id_for_update(self, *, run_id: UUID) -> Run | None: ...

    async def get_by_client_request_id(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        client_request_id: str,
    ) -> Run | None: ...

    async def save(self, run: Run) -> Run: ...

    async def add_transition(self, transition: RunTransitionRecord) -> RunTransitionRecord: ...


class RunEventStore(Protocol):
    async def append(
        self,
        *,
        run_id: UUID,
        event_type: RunEventType,
        audience: RunEventAudience,
        level: RunEventLevel,
        status: str,
        stage: str | None,
        message: str,
        payload_json: dict[str, Any] | None,
        retry_count: int,
        cancel_requested: bool,
        created_at: datetime,
        event_key: str | None,
    ) -> RunEventRecord: ...

    async def list_for_run(
        self,
        *,
        run_id: UUID,
        after_event_number: int | None,
    ) -> list[RunEventRecord]: ...


class RunCheckpointStore(Protocol):
    async def append(
        self,
        *,
        run_id: UUID,
        stage: RunStage,
        checkpoint_key: str,
        payload_json: dict[str, Any] | None,
        summary_json: dict[str, Any] | None,
        created_at: datetime,
    ) -> RunCheckpointRecord: ...

    async def latest_for_run(self, *, run_id: UUID) -> RunCheckpointRecord | None: ...

    async def list_for_run(self, *, run_id: UUID) -> list[RunCheckpointRecord]: ...


class RunQueueBackend(Protocol):
    async def enqueue(
        self,
        *,
        tenant_id: UUID,
        run_id: UUID,
        available_at: datetime,
    ) -> RunQueueItem: ...

    async def claim_available(
        self,
        *,
        now: datetime,
        lease_duration: timedelta,
        limit: int,
        max_attempts: int,
    ) -> list[RunQueueItem]: ...

    async def heartbeat(
        self,
        *,
        queue_item_id: UUID,
        lease_token: UUID,
        lease_expires_at: datetime,
    ) -> bool: ...

    async def complete(
        self,
        *,
        queue_item_id: UUID,
        lease_token: UUID,
        completed_at: datetime,
    ) -> bool: ...

    async def release(
        self,
        *,
        queue_item_id: UUID,
        lease_token: UUID,
        available_at: datetime,
        last_error: str | None,
    ) -> bool: ...

    async def cancel_active_for_run(self, *, run_id: UUID, canceled_at: datetime) -> None: ...


class RunExecutionOrchestrator(Protocol):
    async def execute(
        self,
        *,
        run: Run,
        queue_item_id: UUID,
        lease_token: UUID,
    ) -> None: ...


class TransactionManager(Protocol):
    def boundary(self) -> AbstractAsyncContextManager[None]: ...


class RunStreamWatcher(Protocol):
    async def sleep(self, seconds: float) -> None: ...
