"""Streams a quick-answer SSE response, saves the assistant message, and emits events.

This runs AFTER the main request transaction is committed. It opens its own
database session to save the assistant message, then yields the SSE bytes.
"""
from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from researchlens.modules.conversations.application.dto import (
    ChatSendStreamContext,
    MessageView,
    to_message_view,
)
from researchlens.modules.conversations.domain import Message, MessageRole, MessageType
from researchlens.modules.conversations.infrastructure.chat_llm_adapter import (
    WEB_SEARCH_TOOL,
    ChatLlmAdapter,
    build_chat_prompt,
    extract_tool_call_query,
)
from researchlens.modules.conversations.infrastructure.message_repository_sql import (
    SqlAlchemyMessageRepository,
)
from researchlens.modules.conversations.infrastructure.web_search_adapter import (
    WebSearchAdapter,
)

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a helpful research assistant with access to a web search tool. "
    "Only use the web_search tool when the question requires current, real-time, "
    "or rapidly-changing information (e.g. recent news, live prices, today's events). "
    "For general knowledge questions answer directly from your own knowledge. "
    "When you do search and have results, base your answer on them and cite sources naturally."
)
_FALLBACK_SYSTEM = "You are a helpful research assistant. Answer concisely and helpfully."
_FALLBACK_ANSWER = "I am having trouble generating a response right now."


def _sse_event(event: str, data: dict[str, Any]) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode()


class QuickAnswerStreamer:
    """Generates the SSE stream for the quick-answer chat path."""

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        llm_adapter: ChatLlmAdapter,
        web_search: WebSearchAdapter,
    ) -> None:
        self._session_factory = session_factory
        self._llm = llm_adapter
        self._search = web_search

    async def stream(
        self,
        ctx: ChatSendStreamContext,
    ) -> AsyncGenerator[bytes, None]:
        answer = _FALLBACK_ANSWER
        metadata: dict[str, Any] = ctx.metadata_json or {}

        try:
            answer, did_search = await self._generate(ctx)
            if did_search:
                metadata = {**metadata, "web_searched": True}
        except Exception:
            logger.exception("QuickAnswerStreamer generation failed conversation=%s", ctx.conversation_id)

        assistant_msg = await self._save_assistant_message(ctx, answer, metadata)
        await self._link_user_reply(ctx, assistant_msg)

        user_view = ctx.user_message
        response_payload = {
            "conversation_id": str(ctx.conversation_id),
            "user_message": _message_view_to_dict(user_view) if user_view else None,
            "assistant_message": _message_view_to_dict(to_message_view(assistant_msg)),
            "pending_action": None,
            "idempotent_replay": False,
        }
        yield _sse_event("answer", response_payload)

    async def _generate(self, ctx: ChatSendStreamContext) -> tuple[str, bool]:
        if not self._llm:
            return _FALLBACK_ANSWER, False

        history_dicts = [
            {"role": m.role, "content_text": m.content_text or ""}
            for m in ctx.history
        ]
        messages = build_chat_prompt(history_dicts, ctx.message)

        if not self._search.is_available():
            text = await self._llm.generate_text(
                [{"role": "system", "content": _FALLBACK_SYSTEM}] + messages,
            )
            return text or _FALLBACK_ANSWER, False

        full_messages = [{"role": "system", "content": _SYSTEM_PROMPT}] + messages
        first = await self._llm.generate_with_tools(full_messages, [WEB_SEARCH_TOOL])
        tool_calls = first.get("tool_calls") or []

        if not tool_calls:
            return (first.get("content") or _FALLBACK_ANSWER).strip(), False

        # Emit web-search status before yielding - caller handles the SSE event
        snippets: list[str] = []
        for tool_call in tool_calls:
            query = extract_tool_call_query(tool_call, ctx.message)
            results = await self._search.search(query)
            snippets.extend(
                f"[{i + 1}] {r.title}: {r.snippet[:300]}"
                for i, r in enumerate(results)
            )

        tool_content = "\n\n".join(snippets) if snippets else "Web search unavailable."
        full_messages.append({
            "role": "assistant",
            "content": first.get("content"),
            "tool_calls": tool_calls,
        })
        full_messages.append({
            "role": "tool",
            "tool_call_id": (tool_calls[0].get("id") or "call_0"),
            "content": tool_content,
        })
        final = await self._llm.generate_with_tools(
            full_messages, [WEB_SEARCH_TOOL], tool_choice="none"
        )
        answer = (final.get("content") or "").strip()
        if not answer:
            answer = await self._llm.generate_text(
                [{"role": "system", "content": _FALLBACK_SYSTEM}] + messages,
            )
        return answer or _FALLBACK_ANSWER, True

    async def stream_with_status(
        self,
        ctx: ChatSendStreamContext,
    ) -> AsyncGenerator[bytes, None]:
        """Like stream() but emits a 'status' event before web search."""
        answer = _FALLBACK_ANSWER
        metadata: dict[str, Any] = ctx.metadata_json or {}
        did_search = False

        try:
            if self._search.is_available():
                history_dicts = [
                    {"role": m.role, "content_text": m.content_text or ""}
                    for m in ctx.history
                ]
                messages = build_chat_prompt(history_dicts, ctx.message)
                full_messages = [{"role": "system", "content": _SYSTEM_PROMPT}] + messages
                first = await self._llm.generate_with_tools(full_messages, [WEB_SEARCH_TOOL])
                tool_calls = first.get("tool_calls") or []

                if tool_calls:
                    yield _sse_event("status", {"type": "status", "message": "Searching the web\u2026"})
                    snippets: list[str] = []
                    for tool_call in tool_calls:
                        query = extract_tool_call_query(tool_call, ctx.message)
                        results = await self._search.search(query)
                        snippets.extend(
                            f"[{i + 1}] {r.title}: {r.snippet[:300]}"
                            for i, r in enumerate(results)
                        )
                    tool_content = "\n\n".join(snippets) if snippets else "Web search unavailable."
                    full_messages.append({"role": "assistant", "content": first.get("content"), "tool_calls": tool_calls})
                    full_messages.append({"role": "tool", "tool_call_id": (tool_calls[0].get("id") or "call_0"), "content": tool_content})
                    final = await self._llm.generate_with_tools(full_messages, [WEB_SEARCH_TOOL], tool_choice="none")
                    answer = (final.get("content") or "").strip() or _FALLBACK_ANSWER
                    did_search = True
                else:
                    answer = (first.get("content") or _FALLBACK_ANSWER).strip()
            else:
                history_dicts = [
                    {"role": m.role, "content_text": m.content_text or ""}
                    for m in ctx.history
                ]
                messages = build_chat_prompt(history_dicts, ctx.message)
                answer = await self._llm.generate_text(
                    [{"role": "system", "content": _FALLBACK_SYSTEM}] + messages,
                )
                answer = answer or _FALLBACK_ANSWER
        except Exception:
            logger.exception("QuickAnswerStreamer generation failed conversation=%s", ctx.conversation_id)

        if did_search:
            metadata = {**metadata, "web_searched": True}

        assistant_msg = await self._save_assistant_message(ctx, answer, metadata)
        await self._link_user_reply(ctx, assistant_msg)

        user_view = ctx.user_message
        response_payload = {
            "conversation_id": str(ctx.conversation_id),
            "user_message": _message_view_to_dict(user_view) if user_view else None,
            "assistant_message": _message_view_to_dict(to_message_view(assistant_msg)),
            "pending_action": None,
            "idempotent_replay": False,
        }
        yield _sse_event("answer", response_payload)

    async def _save_assistant_message(
        self,
        ctx: ChatSendStreamContext,
        answer: str,
        metadata: dict[str, Any],
    ) -> Message:
        now = datetime.now(tz=UTC)
        async with self._session_factory() as session:
            repo = SqlAlchemyMessageRepository(session)
            msg = Message.create(
                id=uuid4(),
                tenant_id=ctx.tenant_id,
                conversation_id=ctx.conversation_id,
                role=MessageRole.ASSISTANT,
                type=MessageType.CHAT,
                content_text=answer,
                content_json=None,
                metadata_json=metadata or None,
                created_at=now,
                client_message_id=None,
            )
            saved = await repo.add(msg)
            await session.commit()
        return saved

    async def _link_user_reply(self, ctx: ChatSendStreamContext, assistant_msg: Message) -> None:
        if ctx.user_message_id is None:
            return
        async with self._session_factory() as session:
            from sqlalchemy import update
            from researchlens.modules.conversations.infrastructure.rows.message_row import MessageRow
            await session.execute(
                update(MessageRow)
                .where(
                    MessageRow.tenant_id == ctx.tenant_id,
                    MessageRow.id == ctx.user_message_id,
                )
                .values(metadata_json={"reply_message_id": str(assistant_msg.id)})
            )
            await session.commit()


def _message_view_to_dict(view: MessageView) -> dict[str, Any]:
    return {
        "id": str(view.id),
        "role": view.role,
        "type": view.type,
        "content_text": view.content_text,
        "content_json": view.content_json,
        "created_at": view.created_at.isoformat() if view.created_at else None,
        "client_message_id": view.client_message_id,
    }
