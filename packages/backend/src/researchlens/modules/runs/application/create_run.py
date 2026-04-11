from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from researchlens.modules.runs.application.dto import CreateRunResult, to_run_summary_view
from researchlens.modules.runs.application.ports import (
    ConversationRunSource,
    ConversationScopeReader,
    MessageScopeReader,
    RunEventStore,
    RunQueueBackend,
    RunRepository,
    TransactionManager,
)
from researchlens.modules.runs.domain import (
    Run,
    RunEventAudience,
    RunEventLevel,
    RunEventType,
    RunStatus,
    RunTransitionRecord,
)
from researchlens.shared.errors import NotFoundError, ValidationError


@dataclass(frozen=True, slots=True)
class CreateRunCommand:
    tenant_id: UUID
    user_id: UUID
    conversation_id: UUID
    source_message_id: UUID | None
    request_text: str
    client_request_id: str | None
    output_type: str


class CreateRunUseCase:
    def __init__(
        self,
        *,
        conversation_scope_reader: ConversationScopeReader,
        message_scope_reader: MessageScopeReader,
        run_repository: RunRepository,
        event_store: RunEventStore,
        queue_backend: RunQueueBackend,
        transaction_manager: TransactionManager,
    ) -> None:
        self._conversation_scope_reader = conversation_scope_reader
        self._message_scope_reader = message_scope_reader
        self._run_repository = run_repository
        self._event_store = event_store
        self._queue_backend = queue_backend
        self._transaction_manager = transaction_manager

    async def execute(self, command: CreateRunCommand) -> CreateRunResult:
        async with self._transaction_manager.boundary():
            source = await self._require_conversation_source(command)
            await self._require_source_message(command)
            replay_result = await self._find_idempotent_replay(command)
            if replay_result is not None:
                return replay_result
            now = datetime.now(tz=UTC)
            run = await self._create_queued_run(
                command=command,
                project_id=source.project_id,
                now=now,
            )
            await self._append_creation_events(run=run, request_text=command.request_text, now=now)
            await self._queue_backend.enqueue(
                tenant_id=run.tenant_id,
                run_id=run.id,
                available_at=now,
            )
            run = await self._run_repository.get_by_id_for_tenant(
                tenant_id=run.tenant_id,
                run_id=run.id,
            ) or run

        return CreateRunResult(run=to_run_summary_view(run), idempotent_replay=False)

    async def _require_conversation_source(
        self,
        command: CreateRunCommand,
    ) -> ConversationRunSource:
        source = await self._conversation_scope_reader.get_conversation_source(
            tenant_id=command.tenant_id,
            conversation_id=command.conversation_id,
        )
        if source is None:
            raise NotFoundError("Conversation was not found.")
        if source.project_id is None:
            raise ValidationError("Conversation must belong to a project before a run can start.")
        return source

    async def _require_source_message(self, command: CreateRunCommand) -> None:
        if command.source_message_id is None:
            return
        has_message = await self._message_scope_reader.message_exists_for_conversation(
            tenant_id=command.tenant_id,
            conversation_id=command.conversation_id,
            message_id=command.source_message_id,
        )
        if not has_message:
            raise NotFoundError("Message was not found.")

    async def _find_idempotent_replay(
        self,
        command: CreateRunCommand,
    ) -> CreateRunResult | None:
        if command.client_request_id is None:
            return None
        existing = await self._run_repository.get_by_client_request_id(
            tenant_id=command.tenant_id,
            conversation_id=command.conversation_id,
            client_request_id=command.client_request_id,
        )
        if existing is None:
            return None
        return CreateRunResult(run=to_run_summary_view(existing), idempotent_replay=True)

    async def _create_queued_run(
        self,
        *,
        command: CreateRunCommand,
        project_id: UUID,
        now: datetime,
    ) -> Run:
        run = Run.create(
            id=uuid4(),
            tenant_id=command.tenant_id,
            project_id=project_id,
            conversation_id=command.conversation_id,
            created_by_user_id=command.user_id,
            output_type=command.output_type,
            trigger_message_id=command.source_message_id,
            client_request_id=command.client_request_id,
            created_at=now,
            updated_at=now,
        )
        run = await self._run_repository.add(run)
        run = await self._run_repository.save(
            run.replace_values(status=RunStatus.QUEUED, updated_at=now)
        )
        await self._run_repository.add_transition(
            RunTransitionRecord(
                id=uuid4(),
                run_id=run.id,
                from_status=RunStatus.CREATED,
                to_status=RunStatus.QUEUED,
                changed_at=now,
                reason="create",
            )
        )
        return run

    async def _append_creation_events(
        self,
        *,
        run: Run,
        request_text: str,
        now: datetime,
    ) -> None:
        stage = run.current_stage.value if run.current_stage is not None else None
        await self._event_store.append(
            run_id=run.id,
            event_type=RunEventType.RUN_CREATED,
            audience=RunEventAudience.STATE,
            level=RunEventLevel.INFO,
            status=RunStatus.CREATED.value,
            stage=stage,
            message="Run created",
            payload_json={"request_text": request_text},
            retry_count=run.retry_count,
            cancel_requested=False,
            created_at=now,
            event_key="run-created",
        )
        await self._event_store.append(
            run_id=run.id,
            event_type=RunEventType.RUN_QUEUED,
            audience=RunEventAudience.STATE,
            level=RunEventLevel.INFO,
            status=run.status.value,
            stage=stage,
            message="Waiting for an available worker",
            payload_json=None,
            retry_count=run.retry_count,
            cancel_requested=False,
            created_at=now,
            event_key="run-queued",
        )
