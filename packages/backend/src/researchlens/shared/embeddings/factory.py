from researchlens.shared.config.embeddings import EmbeddingsSettings
from researchlens.shared.embeddings.ports import EmbeddingClient
from researchlens.shared.embeddings.providers.openai_embedding_provider import OpenAiEmbeddingClient


def build_embedding_client(settings: EmbeddingsSettings) -> EmbeddingClient:
    if settings.provider == "openai":
        return OpenAiEmbeddingClient(settings)
    raise ValueError(f"Unsupported embedding provider: {settings.provider}")
