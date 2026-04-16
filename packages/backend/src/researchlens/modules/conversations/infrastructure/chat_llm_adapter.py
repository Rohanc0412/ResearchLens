"""OpenAI chat completions adapter for the conversational chat flow.

Uses the Chat Completions API (not the Responses API) because tool calling
and multi-turn message passing are better supported in that interface.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_CHAT_COMPLETIONS_PATH = "/chat/completions"


class ChatLlmAdapter:
    """Wraps OpenAI-compatible chat completions API with optional tool calling."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def generate_text(
        self,
        messages: list[dict[str, Any]],
        *,
        max_tokens: int = 10000,
        temperature: float = 0.4,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        data = await self._post(payload)
        return _extract_content(data)

    async def generate_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        *,
        tool_choice: str = "auto",
        max_tokens: int = 10000,
        temperature: float = 0.4,
    ) -> dict[str, Any]:
        """Return the raw first choice message dict (including tool_calls if any)."""
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        data = await self._post(payload)
        choices = data.get("choices") or []
        if not choices:
            return {"content": "", "tool_calls": []}
        choice = choices[0]
        msg = choice.get("message") or {}
        return {
            "content": msg.get("content") or "",
            "tool_calls": msg.get("tool_calls") or [],
        }

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{_CHAT_COMPLETIONS_PATH}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()


def _extract_content(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    msg = (choices[0].get("message") or {})
    return (msg.get("content") or "").strip()


def build_chat_prompt(
    history: list[dict[str, str]],
    message: str,
) -> list[dict[str, str]]:
    """Convert message history into the OpenAI messages format."""
    messages: list[dict[str, str]] = []
    for item in history:
        role = item.get("role", "user")
        content = (item.get("content_text") or item.get("content") or "").strip()
        if content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})
    return messages


WEB_SEARCH_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for current information. Use when the question requires "
            "up-to-date facts, recent events, or information beyond your training data."
        ),
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query"}},
            "required": ["query"],
        },
    },
}


def extract_tool_call_query(tool_call: dict[str, Any], fallback: str) -> str:
    fn = tool_call.get("function") or {}
    raw_args = fn.get("arguments") or {}
    if isinstance(raw_args, str):
        try:
            raw_args = json.loads(raw_args)
        except Exception:
            raw_args = {}
    return str(raw_args.get("query") or fallback)
