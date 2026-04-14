import json
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
        raw_text = _extract_output_text_from_response(data)
        return StructuredGenerationResult(
            data=_extract_structured_json(data),
            raw_text=raw_text,
        )

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
    schema = _schema_by_name().get(schema_name)
    if schema is None:
        return None
    return {
        "type": "json_schema",
        "name": schema_name,
        "schema": schema,
        "strict": True,
    }


def _schema_by_name() -> dict[str, dict[str, Any]]:
    string = {"type": "string", "minLength": 1}
    uuid_string = {"type": "string", "format": "uuid"}
    string_array = {"type": "array", "items": {"type": "string"}}
    uuid_array = {"type": "array", "items": uuid_string}
    return {
        "drafting_section": {
            "type": "object",
            "properties": {
                "section_id": string,
                "section_text": string,
                "section_summary": string,
                "status": {"type": "string", "enum": ["completed"]},
            },
            "required": ["section_id", "section_text", "section_summary", "status"],
            "additionalProperties": False,
        },
        "repair_section": {
            "type": "object",
            "properties": {
                "section_id": string,
                "revised_text": string,
                "revised_summary": string,
                "addressed_issue_ids": uuid_array,
                "citations_used": uuid_array,
                "self_check": string,
            },
            "required": [
                "section_id",
                "revised_text",
                "revised_summary",
                "addressed_issue_ids",
                "citations_used",
                "self_check",
            ],
            "additionalProperties": False,
        },
        "retrieval_query_plan": {
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "intent": string,
                            "query": string,
                            "target_section": {"type": ["string", "null"]},
                        },
                        "required": ["intent", "query", "target_section"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["queries"],
            "additionalProperties": False,
        },
        "retrieval_outline": {
            "type": "object",
            "properties": {
                "report_title": string,
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "section_id": string,
                            "title": string,
                            "goal": string,
                            "suggested_evidence_themes": string_array,
                            "key_points": string_array,
                            "section_order": {"type": "integer", "minimum": 1},
                        },
                        "required": [
                            "section_id",
                            "title",
                            "goal",
                            "suggested_evidence_themes",
                            "key_points",
                            "section_order",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["report_title", "sections"],
            "additionalProperties": False,
        },
        "evaluation_claim_verdicts": {
            "type": "object",
            "properties": {
                "claims": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "claim_index": {"type": "integer", "minimum": 1},
                            "claim_text": string,
                            "verdict": {
                                "type": "string",
                                "enum": [
                                    "supported",
                                    "missing_citation",
                                    "invalid_citation",
                                    "overstated",
                                    "unsupported",
                                    "contradicted",
                                ],
                            },
                            "cited_chunk_ids": uuid_array,
                            "supported_chunk_ids": uuid_array,
                            "rationale": string,
                            "repair_hint": string,
                        },
                        "required": [
                            "claim_index",
                            "claim_text",
                            "verdict",
                            "cited_chunk_ids",
                            "supported_chunk_ids",
                            "rationale",
                            "repair_hint",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["claims"],
            "additionalProperties": False,
        },
    }
