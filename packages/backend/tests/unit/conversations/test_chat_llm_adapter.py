import httpx
import pytest

from researchlens.modules.conversations.infrastructure.chat_llm_adapter import (
    ChatLlmAdapter,
)


def build_adapter(handler: httpx.MockTransport) -> ChatLlmAdapter:
    class TestChatLlmAdapter(ChatLlmAdapter):
        async def _post(self, payload: dict[str, object]) -> dict[str, object]:
            async with httpx.AsyncClient(
                transport=handler,
                base_url="https://api.openai.test/v1",
            ) as client:
                response = await client.post("/chat/completions", json=payload)
                response.raise_for_status()
                return response.json()

    return TestChatLlmAdapter(
        api_key="test-key",
        model="gpt-5-nano",
        base_url="https://api.openai.test/v1",
    )


@pytest.mark.asyncio
async def test_generate_text_uses_low_reasoning_for_gpt5_models() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["json"] = request.read().decode()
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Hello"}}]},
        )

    adapter = build_adapter(httpx.MockTransport(handler))

    result = await adapter.generate_text([{"role": "user", "content": "Hi"}])

    assert result == "Hello"
    assert '"model":"gpt-5-nano"' in seen["json"]
    assert '"max_completion_tokens":10000' in seen["json"]
    assert '"max_tokens"' not in seen["json"]
    assert '"temperature"' not in seen["json"]
    assert '"reasoning_effort":"low"' in seen["json"]


@pytest.mark.asyncio
async def test_generate_with_tools_uses_requested_model_override() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["json"] = request.read().decode()
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Hello", "tool_calls": []}}]},
        )

    adapter = build_adapter(httpx.MockTransport(handler))
    adapter._model = "gpt-4.1-mini"

    result = await adapter.generate_with_tools(
        [{"role": "user", "content": "Hi"}],
        [{"type": "function", "function": {"name": "tool", "parameters": {"type": "object"}}}],
        model="gpt-5-nano",
    )

    assert result == {"content": "Hello", "tool_calls": []}
    assert '"model":"gpt-5-nano"' in seen["json"]
    assert '"max_completion_tokens":10000' in seen["json"]
    assert '"max_tokens"' not in seen["json"]
    assert '"temperature"' not in seen["json"]
    assert '"reasoning_effort":"low"' in seen["json"]


@pytest.mark.asyncio
async def test_generate_text_skips_reasoning_for_non_gpt5_models() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["json"] = request.read().decode()
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Hello"}}]},
        )

    adapter = build_adapter(httpx.MockTransport(handler))
    adapter._model = "gpt-4.1-mini"

    await adapter.generate_text([{"role": "user", "content": "Hi"}])

    assert '"max_tokens":10000' in seen["json"]
    assert '"max_completion_tokens"' not in seen["json"]
    assert '"temperature":0.4' in seen["json"]
    assert '"reasoning_effort"' not in seen["json"]
