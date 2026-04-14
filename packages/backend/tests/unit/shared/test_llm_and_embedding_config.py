import httpx
import pytest

from researchlens.shared.config.embeddings import EmbeddingsSettings
from researchlens.shared.config.llm import LlmSettings
from researchlens.shared.embeddings.domain import EmbeddingRequest
from researchlens.shared.embeddings.factory import build_embedding_client
from researchlens.shared.embeddings.providers.openai_embedding_provider import OpenAiEmbeddingClient
from researchlens.shared.llm.domain import StructuredGenerationRequest
from researchlens.shared.llm.factory import build_llm_client
from researchlens.shared.llm.providers.openai_provider import OpenAiStructuredGenerationClient


def test_llm_defaults_to_phase_6_model_and_factory_uses_port() -> None:
    settings = LlmSettings(provider="openai", api_key="test-key")

    client = build_llm_client(settings)

    assert settings.model == "gpt-5-nano"
    assert client.model == "gpt-5-nano"


def test_embeddings_default_to_phase_6_model_and_factory_uses_port() -> None:
    settings = EmbeddingsSettings(provider="openai", api_key="test-key")

    client = build_embedding_client(settings)

    assert settings.model == "text-embedding-3-small"
    assert client.model == "text-embedding-3-small"


@pytest.mark.asyncio
async def test_openai_llm_adapter_maps_responses_request() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["json"] = request.read().decode()
        return httpx.Response(200, json={"output_json": {"ok": True}})

    client = OpenAiStructuredGenerationClient(
        LlmSettings(provider="openai", api_key="test-key"),
        client=httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://api.openai.test/v1",
        ),
    )

    result = await client.generate_structured(
        StructuredGenerationRequest(schema_name="drafting_section", prompt="Prompt")
    )

    assert result.data == {"ok": True}
    assert "gpt-5-nano" in str(seen["json"])
    assert '"max_output_tokens":15000' in str(seen["json"])
    assert '"temperature"' not in str(seen["json"])
    assert '"reasoning":{"effort":"low"}' in str(seen["json"])
    assert '"type":"json_schema"' in str(seen["json"])
    assert '"name":"drafting_section"' in str(seen["json"])


@pytest.mark.asyncio
async def test_openai_llm_adapter_includes_temperature_for_non_gpt5_models() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["json"] = request.read().decode()
        return httpx.Response(200, json={"output_json": {"ok": True}})

    client = OpenAiStructuredGenerationClient(
        LlmSettings(
            provider="openai",
            api_key="test-key",
            model="gpt-4.1-mini",
            temperature=0.7,
        ),
        client=httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://api.openai.test/v1",
        ),
    )

    await client.generate_structured(
        StructuredGenerationRequest(schema_name="schema", prompt="Prompt")
    )

    assert '"temperature":0.7' in str(seen["json"])
    assert '"reasoning"' not in str(seen["json"])


@pytest.mark.asyncio
async def test_openai_llm_adapter_parses_json_from_output_text() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "output_text": (
                    '{"section_id":"overview","section_text":"Body [[chunk:'
                    '00000000-0000-0000-0000-000000000001]]","section_summary":"Bridge","status":"completed"}'
                )
            },
        )

    client = OpenAiStructuredGenerationClient(
        LlmSettings(provider="openai", api_key="test-key"),
        client=httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://api.openai.test/v1",
        ),
    )

    result = await client.generate_structured(
        StructuredGenerationRequest(schema_name="schema", prompt="Prompt")
    )

    assert result.data["section_id"] == "overview"


@pytest.mark.asyncio
async def test_openai_llm_adapter_parses_nested_output_text_from_responses_api() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": (
                                    '{"sections":[{"section_id":"overview","title":"Overview"}]}'
                                ),
                            }
                        ],
                    }
                ]
            },
        )

    client = OpenAiStructuredGenerationClient(
        LlmSettings(provider="openai", api_key="test-key"),
        client=httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://api.openai.test/v1",
        ),
    )

    result = await client.generate_structured(
        StructuredGenerationRequest(schema_name="schema", prompt="Prompt")
    )

    assert result.data["sections"][0]["section_id"] == "overview"


@pytest.mark.asyncio
async def test_openai_llm_adapter_parses_output_parsed_payload() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "output_parsed": {
                    "section_id": "overview",
                    "section_text": "Body [[chunk:00000000-0000-0000-0000-000000000001]]",
                    "section_summary": "Bridge",
                    "status": "completed",
                }
            },
        )

    client = OpenAiStructuredGenerationClient(
        LlmSettings(provider="openai", api_key="test-key"),
        client=httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://api.openai.test/v1",
        ),
    )

    result = await client.generate_structured(
        StructuredGenerationRequest(schema_name="drafting_section", prompt="Prompt")
    )

    assert result.data["status"] == "completed"


@pytest.mark.asyncio
async def test_openai_llm_adapter_retries_read_timeout_and_succeeds() -> None:
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise httpx.ReadTimeout("timed out")
        return httpx.Response(200, json={"output_json": {"ok": True}})

    client = OpenAiStructuredGenerationClient(
        LlmSettings(provider="openai", api_key="test-key"),
        client=httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://api.openai.test/v1",
        ),
    )

    result = await client.generate_structured(
        StructuredGenerationRequest(schema_name="drafting_section", prompt="Prompt")
    )

    assert result.data == {"ok": True}
    assert attempts == 3


@pytest.mark.asyncio
async def test_openai_llm_adapter_retries_retryable_http_status() -> None:
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, json={"error": {"message": "rate limited"}})
        return httpx.Response(200, json={"output_json": {"ok": True}})

    client = OpenAiStructuredGenerationClient(
        LlmSettings(provider="openai", api_key="test-key"),
        client=httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://api.openai.test/v1",
        ),
    )

    result = await client.generate_structured(
        StructuredGenerationRequest(schema_name="drafting_section", prompt="Prompt")
    )

    assert result.data == {"ok": True}
    assert attempts == 2


@pytest.mark.asyncio
async def test_openai_llm_adapter_does_not_retry_non_retryable_http_status() -> None:
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(400, json={"error": {"message": "bad request"}})

    client = OpenAiStructuredGenerationClient(
        LlmSettings(provider="openai", api_key="test-key"),
        client=httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://api.openai.test/v1",
        ),
    )

    with pytest.raises(httpx.HTTPStatusError):
        await client.generate_structured(
            StructuredGenerationRequest(schema_name="drafting_section", prompt="Prompt")
        )

    assert attempts == 1


@pytest.mark.asyncio
async def test_openai_embedding_adapter_maps_batched_request() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["json"] = request.read().decode()
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": 1, "embedding": [2.0]},
                    {"index": 0, "embedding": [1.0]},
                ]
            },
        )

    client = OpenAiEmbeddingClient(
        EmbeddingsSettings(provider="openai", api_key="test-key"),
        client=httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://api.openai.test/v1",
        ),
    )

    result = await client.embed(EmbeddingRequest(texts=("a", "bb")))

    assert result.vectors == ((1.0,), (2.0,))
    assert "text-embedding-3-small" in str(seen["json"])
