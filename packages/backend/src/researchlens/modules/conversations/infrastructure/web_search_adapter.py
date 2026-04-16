"""Tavily web search adapter for chat-time web retrieval."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

TAVILY_API_URL = "https://api.tavily.com/search"


@dataclass(frozen=True)
class WebSearchResult:
    title: str
    url: str
    snippet: str


class WebSearchAdapter:
    """Calls the Tavily search API.

    Returns an empty list when TAVILY_API_KEY is not set (graceful no-op).
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.getenv("TAVILY_API_KEY", "").strip()

    def is_available(self) -> bool:
        return bool(self._api_key)

    async def search(self, query: str, *, max_results: int = 3) -> list[WebSearchResult]:
        if not self._api_key:
            return []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    TAVILY_API_URL,
                    json={"api_key": self._api_key, "query": query, "max_results": max_results},
                )
                response.raise_for_status()
                data = response.json()
            return [
                WebSearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    snippet=r.get("content", ""),
                )
                for r in (data.get("results") or [])[:max_results]
            ]
        except Exception:
            logger.warning("Web search failed for query %r", query, exc_info=True)
            return []
