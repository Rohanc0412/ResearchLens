import httpx

from researchlens.shared.config.embeddings import EmbeddingsSettings
from researchlens.shared.embeddings.domain import EmbeddingRequest, EmbeddingResult


class OpenAiEmbeddingClient:
    def __init__(
        self,
        settings: EmbeddingsSettings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._client = client

    @property
    def model(self) -> str:
        return self._settings.model

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        if not self._settings.api_key:
            raise ValueError("Embedding API key is required for OpenAI embeddings.")
        payload = {"model": self._settings.model, "input": list(request.texts)}
        headers = {"Authorization": f"Bearer {self._settings.api_key}"}
        base_url = self._settings.base_url or "https://api.openai.com/v1"
        if self._client is not None:
            response = await self._client.post("/embeddings", json=payload, headers=headers)
            response.raise_for_status()
        else:
            async with httpx.AsyncClient(timeout=self._settings.timeout_seconds) as client:
                response = await client.post(
                    f"{base_url}/embeddings",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
        rows = sorted(response.json().get("data", []), key=lambda item: item["index"])
        return EmbeddingResult(
            vectors=tuple(tuple(float(value) for value in row["embedding"]) for row in rows)
        )
