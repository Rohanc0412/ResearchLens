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
        StructuredGenerationRequest(schema_name="schema", prompt="Prompt")
    )

    assert result.data == {"ok": True}
    assert "gpt-5-nano" in str(seen["json"])


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
