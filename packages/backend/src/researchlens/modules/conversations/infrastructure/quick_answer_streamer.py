"""Streams a quick-answer SSE response, saves the assistant message, and emits events.

This runs AFTER the main request transaction is committed. It opens its own
database session to save the assistant message, then yields the SSE bytes.
"""
from __future__ import annotations

import json
import logging
import re
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
_SEARCH_RESULT_SYSTEM_PROMPT = (
    "You have already used the web_search tool and received current web results. "
    "Answer using only the information supported by those results. Do not rely on unstated "
    "background knowledge for time-sensitive claims. Every factual paragraph or bullet must "
    "include at least one citation in the form [1], [2], etc. End with a short 'Sources:' "
    "list that maps each cited result number to its URL. Do not say that you lack real-time "
    "access, cannot browse, or cannot access current information. If the search results are "
    "empty or insufficient, say that you could not verify the answer from the available web "
    "results."
)
_SEARCH_RESULT_REPAIR_PROMPT = (
    "Rewrite the draft answer so it complies with the grounding rules. Use only the provided "
    "web search results, cite factual statements with [n], and end with a 'Sources:' list. "
    "Remove any claim that you cannot access current information."
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
                model=ctx.llm_model,
            )
            return text or _FALLBACK_ANSWER, False

        full_messages = [{"role": "system", "content": _SYSTEM_PROMPT}] + messages
        first = await self._llm.generate_with_tools(
            full_messages,
            [WEB_SEARCH_TOOL],
            model=ctx.llm_model,
        )
        tool_calls = first.get("tool_calls") or []

        if not tool_calls:
            return (first.get("content") or _FALLBACK_ANSWER).strip(), False

        answer = await self._complete_search_answer(
            messages=messages,
            ctx=ctx,
            first=first,
            tool_calls=tool_calls,
        )
        if not answer:
            answer = await self._llm.generate_text(
                [{"role": "system", "content": _FALLBACK_SYSTEM}] + messages,
                model=ctx.llm_model,
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
                first = await self._llm.generate_with_tools(
                    full_messages,
                    [WEB_SEARCH_TOOL],
                    model=ctx.llm_model,
                )
                tool_calls = first.get("tool_calls") or []

                if tool_calls:
                    yield _sse_event("status", {"type": "status", "message": "Searching the web\u2026"})
                    answer = await self._complete_search_answer(
                        messages=messages,
                        ctx=ctx,
                        first=first,
                        tool_calls=tool_calls,
                    )
                    answer = answer or _FALLBACK_ANSWER
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
                    model=ctx.llm_model,
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

    async def _complete_search_answer(
        self,
        *,
        messages: list[dict[str, str]],
        ctx: ChatSendStreamContext,
        first: dict[str, Any],
        tool_calls: list[dict[str, Any]],
    ) -> str:
        search_results = await self._collect_search_results(tool_calls, ctx.message)
        tool_content = _build_tool_content(search_results)
        final_messages: list[dict[str, Any]] = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "system", "content": _SEARCH_RESULT_SYSTEM_PROMPT},
            *messages,
            {
                "role": "assistant",
                "content": first.get("content"),
                "tool_calls": tool_calls,
            },
            {
                "role": "tool",
                "tool_call_id": (tool_calls[0].get("id") or "call_0"),
                "content": tool_content,
            },
        ]
        final = await self._llm.generate_with_tools(
            final_messages,
            [WEB_SEARCH_TOOL],
            model=ctx.llm_model,
            tool_choice="none",
        )
        answer = (final.get("content") or "").strip()
        if search_results and _answer_needs_grounding_repair(answer):
            answer = await self._repair_grounded_answer(
                question=ctx.message,
                draft_answer=answer,
                tool_content=tool_content,
                model=ctx.llm_model,
            )
        if search_results and _answer_needs_grounding_repair(answer):
            return _build_grounded_fallback(search_results)
        if search_results:
            answer = _normalize_grounded_answer(answer, search_results)
        return answer

    async def _collect_search_results(
        self,
        tool_calls: list[dict[str, Any]],
        fallback_query: str,
    ) -> list[dict[str, str]]:
        search_results: list[dict[str, str]] = []
        for tool_call in tool_calls:
            query = extract_tool_call_query(tool_call, fallback_query)
            results = await self._search.search(query)
            search_results.extend(
                {
                    "title": getattr(result, "title", ""),
                    "url": getattr(result, "url", ""),
                    "snippet": getattr(result, "snippet", "")[:300],
                }
                for result in results
            )
        return search_results

    async def _repair_grounded_answer(
        self,
        *,
        question: str,
        draft_answer: str,
        tool_content: str,
        model: str | None,
    ) -> str:
        repaired = await self._llm.generate_text(
            [
                {"role": "system", "content": _SEARCH_RESULT_SYSTEM_PROMPT},
                {"role": "system", "content": _SEARCH_RESULT_REPAIR_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"User question:\n{question}\n\n"
                        f"Web search results:\n{tool_content}\n\n"
                        f"Draft answer:\n{draft_answer}"
                    ),
                },
            ],
            model=model,
        )
        return (repaired or "").strip()

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


def _build_tool_content(search_results: list[dict[str, str]]) -> str:
    if not search_results:
        return "Web search unavailable."
    return "\n\n".join(
        _format_search_result(index, result["title"], result["url"], result["snippet"])
        for index, result in enumerate(search_results, start=1)
    )


def _format_search_result(index: int, title: str, url: str, snippet: str) -> str:
    return "\n".join(
        [
            f"[{index}]",
            f"Title: {title}",
            f"URL: {url or 'Unavailable'}",
            f"Snippet: {snippet[:300]}",
        ]
    )


def _answer_needs_grounding_repair(answer: str) -> bool:
    if not answer.strip():
        return True
    if not re.search(r"\[\d+\]", answer):
        return True
    if "Sources:" not in answer:
        return True
    lowered = answer.lower()
    disallowed_phrases = (
        "don't have real-time access",
        "do not have real-time access",
        "cannot browse",
        "can't browse",
        "cannot access current information",
        "can't access current information",
    )
    return any(phrase in lowered for phrase in disallowed_phrases)


def _normalize_grounded_answer(answer: str, search_results: list[dict[str, str]]) -> str:
    body = re.split(r"\n\s*Sources:\s*", answer, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    citations = _extract_citation_numbers(body)
    if not citations:
        return body
    sources_lines = [
        f"- [{index}] {search_results[index - 1]['url'] or 'Unavailable'}"
        for index in citations
        if 1 <= index <= len(search_results)
    ]
    if not sources_lines:
        return body
    return f"{body}\n\nSources:\n" + "\n".join(sources_lines)


def _extract_citation_numbers(text: str) -> list[int]:
    seen: set[int] = set()
    citations: list[int] = []
    for match in re.finditer(r"\[(\d+)\]", text):
        index = int(match.group(1))
        if index in seen:
            continue
        seen.add(index)
        citations.append(index)
    return citations


def _build_grounded_fallback(search_results: list[dict[str, str]]) -> str:
    highlights = "; ".join(
        f"{result['title']} [{index}]"
        for index, result in enumerate(search_results[:3], start=1)
    )
    sources = "\n".join(
        f"- [{index}] {result['url'] or 'Unavailable'}"
        for index, result in enumerate(search_results[:3], start=1)
    )
    return (
        "I found current web results, but I could not fully verify a stronger synthesis from "
        f"them. The available sources highlight: {highlights}.\n\nSources:\n{sources}"
    )
