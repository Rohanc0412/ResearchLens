from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from researchlens.modules.conversations.application.dto import (
    ChatSendImmediateResult,
    ChatSendResult,
    ChatSendStreamContext,
    MessageView,
    to_message_view,
)
from researchlens.modules.conversations.application.ports import (
    ConversationRepository,
    MessageRepository,
    TransactionManager,
)
from researchlens.modules.conversations.domain import (
    Conversation,
    Message,
    MessageRole,
    MessageType,
    classify_chat_intent,
    greeting_response,
    is_greeting,
    parse_consent_reply,
)
from researchlens.shared.errors import NotFoundError

logger = logging.getLogger(__name__)

ACTION_PREFIX = "__ACTION__:"
ACTION_RUN_PIPELINE = "run_pipeline"
ACTION_QUICK_ANSWER = "quick_answer"
PIPELINE_OFFER_LOOK_BACK = 10
PENDING_ACTION_RESEARCH_RUN_OFFER = "research_run_offer"
PENDING_ACTION_START_RESEARCH_RUN = "start_research_run"


@dataclass(frozen=True, slots=True)
class SendChatMessageCommand:
    tenant_id: UUID
    user_id: UUID
    conversation_id: UUID
    message: str
    client_message_id: str
    llm_model: str | None = None
    force_pipeline: bool = False


class SendChatMessageUseCase:
    def __init__(
        self,
        *,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._conv_repo = conversation_repository
        self._msg_repo = message_repository
        self._tx = transaction_manager

    async def execute(self, command: SendChatMessageCommand) -> ChatSendResult:
        async with self._tx.boundary():
            conversation = await self._require_conversation(command)
            replay = await self._idempotent_replay(command, conversation)
            if replay is not None:
                return replay
            return await self._process(command, conversation)

    async def _require_conversation(self, command: SendChatMessageCommand) -> Conversation:
        conversation = await self._conv_repo.get_by_id_for_tenant(
            tenant_id=command.tenant_id,
            conversation_id=command.conversation_id,
        )
        if conversation is None:
            raise NotFoundError("Conversation was not found.")
        return conversation

    async def _idempotent_replay(
        self,
        command: SendChatMessageCommand,
        conversation: Conversation,
    ) -> ChatSendImmediateResult | None:
        existing = await self._msg_repo.get_by_client_message_id(
            tenant_id=command.tenant_id,
            conversation_id=command.conversation_id,
            client_message_id=command.client_message_id,
        )
        if existing is None:
            return None
        reply_id = (existing.metadata_json or {}).get("reply_message_id")
        assistant: Message | None = None
        if reply_id:
            assistant = await self._msg_repo.get_by_id_for_tenant(
                tenant_id=command.tenant_id,
                conversation_id=command.conversation_id,
                message_id=UUID(str(reply_id)),
            )
        pending = _pending_action_from_assistant(assistant)
        if pending is None:
            pending = await self._find_pending_action(command)
        return ChatSendImmediateResult(
            user_message=to_message_view(existing),
            assistant_message=to_message_view(assistant) if assistant else None,
            pending_action=pending,
            idempotent_replay=True,
        )

    async def _process(
        self,
        command: SendChatMessageCommand,
        conversation: Conversation,
    ) -> ChatSendResult:
        action_id = _parse_action_id(command.message)
        user_msg = await self._save_user_message(command, action_id)
        now = datetime.now(tz=UTC)

        if command.force_pipeline and action_id is None:
            return await self._handle_force_pipeline(command, user_msg, now)

        if action_id is not None:
            return await self._handle_action(command, user_msg, action_id, now)

        if is_greeting(command.message):
            return await self._handle_greeting(command, user_msg, now)

        pending = await self._find_pending_action(command)
        if pending is not None:
            return await self._handle_consent(command, user_msg, pending, now)

        decision = classify_chat_intent(command.message)
        if decision.mode == "offer_pipeline" and decision.confidence >= 0.75:
            return await self._handle_pipeline_offer(command, user_msg, decision, now)

        history = await self._msg_repo.list_recent_chat(
            tenant_id=command.tenant_id,
            conversation_id=command.conversation_id,
            limit=6,
            exclude_message_id=user_msg.id,
        )
        return ChatSendStreamContext(
            user_message=to_message_view(user_msg),
            conversation_id=command.conversation_id,
            tenant_id=command.tenant_id,
            user_message_id=user_msg.id,
            history=[to_message_view(m) for m in history],
            message=command.message,
            llm_model=command.llm_model,
            metadata_json={"router": {"mode": decision.mode, "confidence": decision.confidence}},
        )

    async def _save_user_message(
        self,
        command: SendChatMessageCommand,
        action_id: str | None,
    ) -> Message:
        now = datetime.now(tz=UTC)
        msg_type = MessageType.ACTION if action_id else MessageType.CHAT
        content_json: dict[str, Any] | None = (
            {"action_id": action_id, "label": _action_label(action_id)} if action_id else None
        )
        msg = Message.create(
            id=uuid4(),
            tenant_id=command.tenant_id,
            conversation_id=command.conversation_id,
            role=MessageRole.USER,
            type=msg_type,
            content_text=command.message,
            content_json=content_json,
            metadata_json=None,
            created_at=_advance_timestamp(now, None),
            client_message_id=command.client_message_id,
        )
        return await self._msg_repo.add(msg)

    async def _find_pending_action(
        self,
        command: SendChatMessageCommand,
    ) -> dict[str, Any] | None:
        recent = await self._msg_repo.list_recent_chat(
            tenant_id=command.tenant_id,
            conversation_id=command.conversation_id,
            limit=PIPELINE_OFFER_LOOK_BACK,
        )
        for msg in reversed(recent):
            if msg.type == MessageType.PIPELINE_OFFER and msg.role == MessageRole.ASSISTANT:
                pending = (msg.content_json or {}).get("pending")
                if isinstance(pending, dict):
                    return pending
        return None

    async def _handle_force_pipeline(
        self,
        command: SendChatMessageCommand,
        user_msg: Message,
        now: datetime,
    ) -> ChatSendResult:
        prompt = command.message.strip()
        pending = _build_run_start_payload(prompt)
        assistant = await self._save_message(
            command,
            role=MessageRole.ASSISTANT,
            type=MessageType.RUN_STARTED,
            content_text="Starting the research pipeline. Open the run panel to track progress.",
            content_json={"question": prompt, "status": "queued"},
            now=now,
        )
        await self._link_reply(command, user_msg, assistant)
        return ChatSendImmediateResult(
            user_message=to_message_view(user_msg),
            assistant_message=to_message_view(assistant),
            pending_action=pending,
        )

    async def _handle_action(
        self,
        command: SendChatMessageCommand,
        user_msg: Message,
        action_id: str,
        now: datetime,
    ) -> ChatSendResult:
        pending = await self._find_pending_action(command)
        if action_id == ACTION_RUN_PIPELINE and pending:
            return await self._handle_run_pipeline_action(command, user_msg, pending, now)
        if action_id == ACTION_QUICK_ANSWER and pending:
            return await self._handle_quick_answer_action(command, user_msg, pending, now)
        assistant = await self._save_message(
            command,
            role=MessageRole.ASSISTANT,
            type=MessageType.CHAT,
            content_text="There is no pending research offer. Ask a new question to begin.",
            now=now,
        )
        await self._link_reply(command, user_msg, assistant)
        return ChatSendImmediateResult(
            user_message=to_message_view(user_msg),
            assistant_message=to_message_view(assistant),
        )

    async def _handle_run_pipeline_action(
        self,
        command: SendChatMessageCommand,
        user_msg: Message,
        pending: dict[str, Any],
        now: datetime,
    ) -> ChatSendImmediateResult:
        prompt = str(pending.get("prompt") or command.message).strip()
        assistant = await self._save_message(
            command,
            role=MessageRole.ASSISTANT,
            type=MessageType.RUN_STARTED,
            content_text="Starting the research pipeline. Open the run panel to track progress.",
            content_json={"question": prompt, "status": "queued"},
            now=now,
        )
        await self._link_reply(command, user_msg, assistant)
        return ChatSendImmediateResult(
            user_message=to_message_view(user_msg),
            assistant_message=to_message_view(assistant),
            pending_action=_build_run_start_payload(prompt),
        )

    async def _handle_quick_answer_action(
        self,
        command: SendChatMessageCommand,
        user_msg: Message,
        pending: dict[str, Any],
        now: datetime,
    ) -> ChatSendStreamContext:
        prompt = str(pending.get("prompt") or command.message).strip()
        history = await self._msg_repo.list_recent_chat(
            tenant_id=command.tenant_id,
            conversation_id=command.conversation_id,
            limit=6,
            exclude_message_id=user_msg.id,
        )
        return ChatSendStreamContext(
            user_message=to_message_view(user_msg),
            conversation_id=command.conversation_id,
            tenant_id=command.tenant_id,
            user_message_id=user_msg.id,
            history=[to_message_view(m) for m in history],
            message=prompt,
            llm_model=command.llm_model,
            metadata_json={"consent": "declined"},
        )

    async def _handle_greeting(
        self,
        command: SendChatMessageCommand,
        user_msg: Message,
        now: datetime,
    ) -> ChatSendImmediateResult:
        assistant = await self._save_message(
            command,
            role=MessageRole.ASSISTANT,
            type=MessageType.CHAT,
            content_text=greeting_response(),
            metadata_json={"fast_path": "greeting"},
            now=now,
        )
        await self._link_reply(command, user_msg, assistant)
        return ChatSendImmediateResult(
            user_message=to_message_view(user_msg),
            assistant_message=to_message_view(assistant),
        )

    async def _handle_consent(
        self,
        command: SendChatMessageCommand,
        user_msg: Message,
        pending: dict[str, Any],
        now: datetime,
    ) -> ChatSendResult:
        decision = parse_consent_reply(command.message, pending.get("prompt"))
        pending_prompt = str(pending.get("prompt") or "").strip()
        pending_model = pending.get("llm_model") or command.llm_model

        if decision == "yes":
            new_pending = _build_offer_pending_payload(pending_prompt, pending_model, now)
            assistant = await self._save_pipeline_offer(
                command,
                new_pending,
                now,
                content_text=(
                    "Select Run research report to start the report, or choose Quick answer "
                    "to stay in chat."
                ),
                prompt_preview=pending_prompt,
            )
            await self._link_reply(command, user_msg, assistant)
            return ChatSendImmediateResult(
                user_message=to_message_view(user_msg),
                assistant_message=to_message_view(assistant),
                pending_action=new_pending,
            )

        if decision == "no":
            history = await self._msg_repo.list_recent_chat(
                tenant_id=command.tenant_id,
                conversation_id=command.conversation_id,
                limit=6,
                exclude_message_id=user_msg.id,
            )
            return ChatSendStreamContext(
                user_message=to_message_view(user_msg),
                conversation_id=command.conversation_id,
                tenant_id=command.tenant_id,
                user_message_id=user_msg.id,
                history=[to_message_view(m) for m in history],
                message=pending_prompt,
                llm_model=pending_model,
                metadata_json={"consent": "declined"},
            )

        if decision == "new_topic":
            history = await self._msg_repo.list_recent_chat(
                tenant_id=command.tenant_id,
                conversation_id=command.conversation_id,
                limit=6,
                exclude_message_id=user_msg.id,
            )
            return ChatSendStreamContext(
                user_message=to_message_view(user_msg),
                conversation_id=command.conversation_id,
                tenant_id=command.tenant_id,
                user_message_id=user_msg.id,
                history=[to_message_view(m) for m in history],
                message=command.message,
                llm_model=command.llm_model,
                metadata_json=None,
            )

        # ambiguous
        ambiguous_count = int(pending.get("ambiguous_count", 0))
        if ambiguous_count >= 1:
            history = await self._msg_repo.list_recent_chat(
                tenant_id=command.tenant_id,
                conversation_id=command.conversation_id,
                limit=6,
                exclude_message_id=user_msg.id,
            )
            return ChatSendStreamContext(
                user_message=to_message_view(user_msg),
                conversation_id=command.conversation_id,
                tenant_id=command.tenant_id,
                user_message_id=user_msg.id,
                history=[to_message_view(m) for m in history],
                message=pending_prompt,
                llm_model=pending_model,
                metadata_json={"consent": "default_quick_answer"},
            )
        new_pending = _build_offer_pending_payload(
            pending_prompt, pending_model, now, ambiguous_count=ambiguous_count + 1
        )
        assistant = await self._save_message(
            command,
            role=MessageRole.ASSISTANT,
            type=MessageType.CHAT,
            content_text="Do you want the full cited research report, or a quick chat answer?",
            metadata_json={"consent": "clarify"},
            now=now,
        )
        await self._link_reply(command, user_msg, assistant)
        return ChatSendImmediateResult(
            user_message=to_message_view(user_msg),
            assistant_message=to_message_view(assistant),
            pending_action=new_pending,
        )

    async def _handle_pipeline_offer(
        self,
        command: SendChatMessageCommand,
        user_msg: Message,
        decision: Any,
        now: datetime,
    ) -> ChatSendImmediateResult:
        pending = _build_offer_pending_payload(command.message, command.llm_model, now)
        assistant = await self._save_pipeline_offer(command, pending, now)
        await self._link_reply(command, user_msg, assistant)
        return ChatSendImmediateResult(
            user_message=to_message_view(user_msg),
            assistant_message=to_message_view(assistant),
            pending_action=pending,
        )

    async def _save_pipeline_offer(
        self,
        command: SendChatMessageCommand,
        pending: dict[str, Any],
        now: datetime,
        *,
        content_text: str | None = None,
        prompt_preview: str | None = None,
    ) -> Message:
        return await self._save_message(
            command,
            role=MessageRole.ASSISTANT,
            type=MessageType.PIPELINE_OFFER,
            content_text=content_text
            or (
                "This looks like a research-style request. "
                "Do you want me to run the research pipeline and generate a cited report?"
            ),
            content_json={
                "offer": {
                    "prompt_preview": (prompt_preview or command.message)[:160],
                    "actions": [
                        {"id": ACTION_RUN_PIPELINE, "label": _action_label(ACTION_RUN_PIPELINE)},
                        {"id": ACTION_QUICK_ANSWER, "label": _action_label(ACTION_QUICK_ANSWER)},
                    ],
                },
                "pending": pending,
            },
            now=now,
        )

    async def _save_message(
        self,
        command: SendChatMessageCommand,
        *,
        role: MessageRole,
        type: MessageType,
        content_text: str | None = None,
        content_json: dict[str, Any] | None = None,
        metadata_json: dict[str, Any] | None = None,
        now: datetime,
    ) -> Message:
        msgs = await self._msg_repo.list_recent_chat(
            tenant_id=command.tenant_id,
            conversation_id=command.conversation_id,
            limit=1,
        )
        last_ts = msgs[-1].created_at if msgs else None
        msg = Message.create(
            id=uuid4(),
            tenant_id=command.tenant_id,
            conversation_id=command.conversation_id,
            role=role,
            type=type,
            content_text=content_text,
            content_json=content_json,
            metadata_json=metadata_json,
            created_at=_advance_timestamp(now, last_ts),
            client_message_id=None,
        )
        return await self._msg_repo.add(msg)

    async def _link_reply(
        self,
        command: SendChatMessageCommand,
        user_msg: Message,
        assistant_msg: Message,
    ) -> None:
        await self._msg_repo.update_metadata(
            tenant_id=command.tenant_id,
            conversation_id=command.conversation_id,
            message_id=user_msg.id,
            metadata_json={"reply_message_id": str(assistant_msg.id)},
        )


def _parse_action_id(message: str) -> str | None:
    if not message.startswith(ACTION_PREFIX):
        return None
    action = message[len(ACTION_PREFIX):].strip().lower()
    return action or None


def _action_label(action_id: str) -> str:
    if action_id == ACTION_RUN_PIPELINE:
        return "Run research report"
    if action_id == ACTION_QUICK_ANSWER:
        return "Quick answer"
    return action_id.replace("_", " ").title()


def _build_offer_pending_payload(
    prompt: str,
    llm_model: str | None,
    now: datetime,
    ambiguous_count: int = 0,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": PENDING_ACTION_RESEARCH_RUN_OFFER,
        "prompt": prompt,
        "created_at": now.isoformat(),
        "ambiguous_count": ambiguous_count,
    }
    if llm_model:
        payload["llm_model"] = llm_model
    return payload


def _build_run_start_payload(prompt: str) -> dict[str, Any]:
    return {
        "type": PENDING_ACTION_START_RESEARCH_RUN,
        "prompt": prompt,
    }


def _pending_action_from_assistant(assistant: Message | None) -> dict[str, Any] | None:
    if assistant is None:
        return None
    if assistant.type is MessageType.RUN_STARTED:
        question = (assistant.content_json or {}).get("question")
        if isinstance(question, str) and question.strip():
            return _build_run_start_payload(question.strip())
    if assistant.type is MessageType.PIPELINE_OFFER:
        pending = (assistant.content_json or {}).get("pending")
        if isinstance(pending, dict):
            return pending
    return None


def _advance_timestamp(now: datetime, last_ts: datetime | None) -> datetime:
    if last_ts is None:
        return now
    if last_ts.tzinfo is None:
        last_ts = last_ts.replace(tzinfo=UTC)
    return last_ts + timedelta(microseconds=1) if now <= last_ts else now
