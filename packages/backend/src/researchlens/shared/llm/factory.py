from researchlens.shared.config.llm import LlmSettings
from researchlens.shared.llm.ports import StructuredGenerationClient
from researchlens.shared.llm.providers.openai_provider import OpenAiStructuredGenerationClient


def build_llm_client(settings: LlmSettings) -> StructuredGenerationClient:
    if settings.provider == "openai":
        return OpenAiStructuredGenerationClient(settings)
    raise ValueError(f"Unsupported LLM provider: {settings.provider}")
