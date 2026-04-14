import asyncio
import json
from typing import Any, cast

import httpx

from researchlens.shared.config.llm import LlmSettings
from researchlens.shared.llm.domain import StructuredGenerationRequest, StructuredGenerationResult
from researchlens.shared.llm.providers.openai_schemas import schema_by_name


class OpenAiStructuredGenerationClient:
    _MAX_RETRIES = 2
    _MIN_TIMEOUT_SECONDS = 60.0

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
        payload: dict[str, Any] = {
            "model": self._settings.model,
            "input": self._messages(request),
            "max_output_tokens": request.max_output_tokens or self._settings.max_output_tokens,
        }
        text_format = _structured_output_format(request.schema_name)
        if text_format is not None:
            payload["text"] = {"format": text_format, "verbosity": "low"}
        if self._uses_reasoning_controls():
            payload["reasoning"] = {"effort": "low"}
        if not self._uses_fixed_temperature():
            payload["temperature"] = self._settings.temperature
        headers = {"Authorization": f"Bearer {self._settings.api_key}"}
        base_url = self._settings.base_url or "https://api.openai.com/v1"
        response = await self._post_with_retries(
            base_url=base_url,
            payload=payload,
            headers=headers,
        )
        data = response.json()
        raw_text = _extract_output_text_from_response(data)
        return StructuredGenerationResult(
            data=_extract_structured_json(data),
            raw_text=raw_text,
        )

    async def _post_with_retries(
        self,
        *,
        base_url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self._MAX_RETRIES + 1):
            try:
                response = await self._post_once(
                    base_url=base_url,
                    payload=payload,
                    headers=headers,
                )
                if not _should_retry_status(response.status_code) or attempt >= self._MAX_RETRIES:
                    response.raise_for_status()
                    return response
                await asyncio.sleep(_retry_delay_seconds(attempt))
                continue
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TransportError) as exc:
                last_error = exc
                if attempt >= self._MAX_RETRIES:
                    raise
                await asyncio.sleep(_retry_delay_seconds(attempt))
        assert last_error is not None
        raise last_error

    async def _post_once(
        self,
        *,
        base_url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> httpx.Response:
        if self._client is not None:
            return await self._client.post("/responses", json=payload, headers=headers)
        async with httpx.AsyncClient(timeout=self._effective_timeout_seconds()) as client:
            return await client.post(
                f"{base_url}/responses",
                json=payload,
                headers=headers,
            )

    def _effective_timeout_seconds(self) -> float:
        return max(self._settings.timeout_seconds, self._MIN_TIMEOUT_SECONDS)

    def _uses_fixed_temperature(self) -> bool:
        return self._settings.model.startswith("gpt-5")

    def _uses_reasoning_controls(self) -> bool:
        return self._settings.model.startswith("gpt-5")

    def _messages(self, request: StructuredGenerationRequest) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        return messages


def _extract_structured_json(data: dict[str, Any]) -> dict[str, Any]:
    if isinstance(data.get("output_parsed"), dict):
        return cast(dict[str, Any], data["output_parsed"])
    if isinstance(data.get("structured"), dict):
        return cast(dict[str, Any], data["structured"])
    if isinstance(data.get("output_json"), dict):
        return cast(dict[str, Any], data["output_json"])
    nested_output_text = _extract_output_text_from_response(data)
    if nested_output_text is not None:
        parsed = _try_parse_json(nested_output_text)
        if parsed is not None:
            return parsed
        return {"raw": nested_output_text}
    output_text = data.get("output_text")
    if isinstance(output_text, str):
        parsed = _try_parse_json(output_text)
        if parsed is not None:
            return parsed
        return {"raw": output_text}
    return data


def _extract_output_text_from_response(data: dict[str, Any]) -> str | None:
    output_text = data.get("output_text")
    if isinstance(output_text, str):
        return output_text
    output = data.get("output")
    if not isinstance(output, list):
        return None
    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            text = part.get("text")
            if part.get("type") == "output_text" and isinstance(text, str):
                return text
            if (
                part.get("type") == "output_text"
                and isinstance(text, dict)
                and isinstance(text.get("value"), str)
            ):
                return cast(str, text["value"])
    return None


def _try_parse_json(value: str) -> dict[str, Any] | None:
    text = value.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _structured_output_format(schema_name: str) -> dict[str, Any] | None:
    schema = schema_by_name().get(schema_name)
    if schema is None:
        return None
    return {
        "type": "json_schema",
        "name": schema_name,
        "schema": schema,
        "strict": True,
    }


def _should_retry_status(status_code: int) -> bool:
    return status_code in {408, 409, 429} or 500 <= status_code <= 599


def _retry_delay_seconds(attempt: int) -> float:
    return 0.25 * (attempt + 1)
