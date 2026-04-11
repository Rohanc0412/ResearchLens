from typing import Any, cast

import httpx

from researchlens.shared.config.llm import LlmSettings
from researchlens.shared.llm.domain import StructuredGenerationRequest, StructuredGenerationResult


class OpenAiStructuredGenerationClient:
    def __init__(
        self,
        settings: LlmSettings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._client = client

    @property
    def model(self) -> str:
        return self._settings.model

    async def generate_structured(
        self,
        request: StructuredGenerationRequest,
    ) -> StructuredGenerationResult:
        if not self._settings.api_key:
            raise ValueError("LLM API key is required for OpenAI generation.")
        payload = {
            "model": self._settings.model,
            "input": self._messages(request),
            "max_output_tokens": request.max_output_tokens or self._settings.max_output_tokens,
            "temperature": self._settings.temperature,
        }
        headers = {"Authorization": f"Bearer {self._settings.api_key}"}
        base_url = self._settings.base_url or "https://api.openai.com/v1"
        if self._client is not None:
            response = await self._client.post("/responses", json=payload, headers=headers)
            response.raise_for_status()
        else:
            async with httpx.AsyncClient(timeout=self._settings.timeout_seconds) as client:
                response = await client.post(
                    f"{base_url}/responses",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
        data = response.json()
        return StructuredGenerationResult(
            data=_extract_structured_json(data),
            raw_text=data.get("output_text"),
        )

    def _messages(self, request: StructuredGenerationRequest) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        return messages


def _extract_structured_json(data: dict[str, Any]) -> dict[str, Any]:
    if isinstance(data.get("structured"), dict):
        return cast(dict[str, Any], data["structured"])
    if isinstance(data.get("output_json"), dict):
        return cast(dict[str, Any], data["output_json"])
    return data
