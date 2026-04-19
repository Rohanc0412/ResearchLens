from datetime import UTC, datetime
from dataclasses import replace
from types import MethodType
from uuid import uuid4

import pytest

from researchlens.modules.conversations.application.dto import (
    ChatSendStreamContext,
    MessageView,
)
from researchlens.modules.conversations.domain import (
    Message,
    MessageRole,
    MessageType,
)
from researchlens.modules.conversations.infrastructure.quick_answer_streamer import (
    QuickAnswerStreamer,
)


class FakeLlmAdapter:
    def __init__(
        self,
        *,
        first: dict | None = None,
        final: dict | None = None,
        text: str = "Plain answer",
    ) -> None:
        self._text = text
        self._first = first or {"content": text, "tool_calls": []}
        self._final = final or {"content": text, "tool_calls": []}
        self.generate_text_calls: list[list[dict[str, str]]] = []
        self.generate_with_tools_calls: list[list[dict[str, object]]] = []
        self.requested_models: list[str | None] = []

    async def generate_text(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
    ) -> str:
        self.generate_text_calls.append(messages)
        self.requested_models.append(model)
        return self._text

    async def generate_with_tools(
        self,
        messages: list[dict[str, object]],
        _tools: list[dict[str, object]],
        *,
        model: str | None = None,
        tool_choice: str = "auto",
    ) -> dict:
        self.generate_with_tools_calls.append(messages)
        self.requested_models.append(model)
        if tool_choice == "none":
            return self._final
        return self._first


class FakeSearchAdapter:
    def __init__(
        self,
        *,
        available: bool,
        results: list[object] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._available = available
        self._results = results or []
        self._error = error
        self.queries: list[str] = []

    def is_available(self) -> bool:
        return self._available

    async def search(self, query: str) -> list[object]:
        self.queries.append(query)
        if self._error is not None:
            raise self._error
        return self._results


def build_context(message: str = "What is the weather today?") -> ChatSendStreamContext:
    timestamp = datetime.now(tz=UTC)
    return ChatSendStreamContext(
        user_message=MessageView(
            id=uuid4(),
            tenant_id=uuid4(),
            conversation_id=uuid4(),
            role="user",
            type="chat",
            content_text=message,
            content_json=None,
            metadata_json=None,
            created_at=timestamp,
            client_message_id="client-1",
        ),
        conversation_id=uuid4(),
        tenant_id=uuid4(),
        user_message_id=uuid4(),
        history=[],
        message=message,
    )


def build_streamer(
    llm: FakeLlmAdapter,
    search: FakeSearchAdapter,
) -> QuickAnswerStreamer:
    return QuickAnswerStreamer(  # type: ignore[arg-type]
        session_factory=None,
        llm_adapter=llm,
        web_search=search,
    )


def patch_persistence(streamer: QuickAnswerStreamer) -> None:
    async def fake_save(
        self: QuickAnswerStreamer,
        ctx: ChatSendStreamContext,
        answer: str,
        metadata: dict[str, object],
    ) -> Message:
        return Message.create(
            id=uuid4(),
            tenant_id=ctx.tenant_id,
            conversation_id=ctx.conversation_id,
            role=MessageRole.ASSISTANT,
            type=MessageType.CHAT,
            content_text=answer,
            content_json=None,
            metadata_json=metadata or None,
            created_at=datetime.now(tz=UTC),
            client_message_id=None,
        )

    async def fake_link(
        self: QuickAnswerStreamer,
        _ctx: ChatSendStreamContext,
        _assistant_msg: Message,
    ) -> None:
        return None

    streamer._save_assistant_message = MethodType(fake_save, streamer)
    streamer._link_user_reply = MethodType(fake_link, streamer)


def build_tool_call(query: str) -> dict:
    return {
        "id": "call-1",
        "function": {"arguments": f'{{"query": "{query}"}}'},
    }


@pytest.mark.asyncio
async def test_generate_returns_direct_answer_without_search() -> None:
    llm = FakeLlmAdapter(first={"content": "Direct answer", "tool_calls": []})
    search = FakeSearchAdapter(available=True)
    streamer = build_streamer(llm, search)

    answer, did_search = await streamer._generate(build_context("Explain transformers."))

    assert answer == "Direct answer"
    assert did_search is False
    assert search.queries == []


@pytest.mark.asyncio
async def test_generate_uses_generate_text_when_search_is_unavailable() -> None:
    llm = FakeLlmAdapter(text="Plain answer without tools")
    search = FakeSearchAdapter(available=False)
    streamer = build_streamer(llm, search)

    answer, did_search = await streamer._generate(build_context("What is Amazon Bedrock?"))

    assert answer == "Plain answer without tools"
    assert did_search is False
    assert len(llm.generate_text_calls) == 1


@pytest.mark.asyncio
async def test_generate_passes_selected_model_to_llm_calls() -> None:
    llm = FakeLlmAdapter(text="Plain answer without tools")
    search = FakeSearchAdapter(available=False)
    streamer = build_streamer(llm, search)
    ctx = replace(build_context("What is Amazon Bedrock?"), llm_model="gpt-5-nano")

    answer, did_search = await streamer._generate(ctx)

    assert answer == "Plain answer without tools"
    assert did_search is False
    assert llm.requested_models == ["gpt-5-nano"]


@pytest.mark.asyncio
async def test_stream_with_status_emits_status_before_answer() -> None:
    llm = FakeLlmAdapter(
        first={"content": "", "tool_calls": [build_tool_call("weather today")]},
        final={
            "content": "It is sunny today [1].\n\nSources:\n- [1] https://weather.example",
            "tool_calls": [],
        },
    )
    result = type("SearchResult", (), {"title": "Weather", "snippet": "Sunny", "url": "https://weather.example"})
    search = FakeSearchAdapter(available=True, results=[result()])
    streamer = build_streamer(llm, search)
    patch_persistence(streamer)

    events = [chunk.decode() async for chunk in streamer.stream_with_status(build_context())]

    assert events[0].startswith("event: status")
    assert "Searching the web" in events[0]
    assert events[1].startswith("event: answer")
    assert "It is sunny today [1]." in events[1]
    assert search.queries == ["weather today"]
    assert "Weather" in llm.generate_with_tools_calls[1][-1]["content"]


@pytest.mark.asyncio
async def test_generate_adds_post_search_instruction_and_urls_to_final_call() -> None:
    llm = FakeLlmAdapter(
        first={"content": "", "tool_calls": [build_tool_call("latest AI news")]},
        final={
            "content": "Search-backed answer [1].\n\nSources:\n- [1] https://example.com/latest-ai",
            "tool_calls": [],
        },
    )
    result = type(
        "SearchResult",
        (),
        {
            "title": "Example Source",
            "snippet": "Fresh result snippet",
            "url": "https://example.com/latest-ai",
        },
    )
    search = FakeSearchAdapter(available=True, results=[result()])
    streamer = build_streamer(llm, search)

    answer, did_search = await streamer._generate(build_context("What are the latest advancements in AI in 2026?"))

    final_messages = llm.generate_with_tools_calls[1]
    assert answer == "Search-backed answer [1].\n\nSources:\n- [1] https://example.com/latest-ai"
    assert did_search is True
    assert final_messages[1]["role"] == "system"
    assert "Answer using only the information supported by those results" in final_messages[1]["content"]
    assert "https://example.com/latest-ai" in final_messages[-1]["content"]


@pytest.mark.asyncio
async def test_generate_repairs_ungrounded_search_answer() -> None:
    llm = FakeLlmAdapter(
        first={"content": "", "tool_calls": [build_tool_call("latest AI news")]},
        final={"content": "I don't have real-time access to current sources.", "tool_calls": []},
        text="Recent coverage highlights integrated AI systems and healthcare uses [1][2].\n\nSources:\n- [1] https://example.com/latest-ai\n- [2] https://example.com/health-ai",
    )
    result = type(
        "SearchResult",
        (),
        {
            "title": "Example Source",
            "snippet": "Fresh result snippet",
            "url": "https://example.com/latest-ai",
        },
    )
    result_two = type(
        "SearchResult",
        (),
        {
            "title": "Health Source",
            "snippet": "Healthcare result snippet",
            "url": "https://example.com/health-ai",
        },
    )
    search = FakeSearchAdapter(available=True, results=[result(), result_two()])
    streamer = build_streamer(llm, search)

    answer, did_search = await streamer._generate(build_context("What are the latest advancements in AI in 2026?"))

    repair_prompt = llm.generate_text_calls[0][-1]["content"]
    assert answer == "Recent coverage highlights integrated AI systems and healthcare uses [1][2].\n\nSources:\n- [1] https://example.com/latest-ai\n- [2] https://example.com/health-ai"
    assert did_search is True
    assert "Draft answer:\nI don't have real-time access to current sources." in repair_prompt
    assert "https://example.com/latest-ai" in repair_prompt


@pytest.mark.asyncio
async def test_generate_normalizes_sources_to_match_citations() -> None:
    llm = FakeLlmAdapter(
        first={"content": "", "tool_calls": [build_tool_call("latest AI news")]},
        final={
            "content": (
                "Integrated systems are a major 2026 trend [1].\n\n"
                "Healthcare deployment is another notable trend [3].\n\n"
                "Sources:\n"
                "- https://wrong.example/one\n"
                "- https://wrong.example/two"
            ),
            "tool_calls": [],
        },
    )
    result_one = type(
        "SearchResult",
        (),
        {
            "title": "Integrated Systems",
            "snippet": "Integrated systems snippet",
            "url": "https://example.com/integrated",
        },
    )
    result_two = type(
        "SearchResult",
        (),
        {
            "title": "Middle Result",
            "snippet": "Middle snippet",
            "url": "https://example.com/middle",
        },
    )
    result_three = type(
        "SearchResult",
        (),
        {
            "title": "Healthcare Result",
            "snippet": "Healthcare snippet",
            "url": "https://example.com/healthcare",
        },
    )
    search = FakeSearchAdapter(available=True, results=[result_one(), result_two(), result_three()])
    streamer = build_streamer(llm, search)

    answer, did_search = await streamer._generate(build_context("What are the latest advancements in AI in 2026?"))

    assert did_search is True
    assert answer == (
        "Integrated systems are a major 2026 trend [1].\n\n"
        "Healthcare deployment is another notable trend [3].\n\n"
        "Sources:\n"
        "- [1] https://example.com/integrated\n"
        "- [3] https://example.com/healthcare"
    )


@pytest.mark.asyncio
async def test_stream_with_status_falls_back_when_search_fails() -> None:
    llm = FakeLlmAdapter(
        first={"content": "", "tool_calls": [build_tool_call("latest pricing")]},
    )
    search = FakeSearchAdapter(
        available=True,
        error=RuntimeError("search failed"),
    )
    streamer = build_streamer(llm, search)
    patch_persistence(streamer)

    events = [chunk.decode() async for chunk in streamer.stream_with_status(build_context())]

    assert events[0].startswith("event: status")
    assert events[1].startswith("event: answer")
    assert "I am having trouble generating a response right now." in events[1]
