import asyncio
from collections.abc import Sequence
from typing import Any


class RagasFaithfulnessScorer:
    _MIN_REASONING_MAX_TOKENS = 8192

    def __init__(
        self,
        *,
        provider: str,
        model: str,
        api_key: str | None,
        base_url: str | None,
        timeout_seconds: float,
        max_tokens: int,
    ) -> None:
        self._provider = provider
        self._model = model
        self._api_key = api_key
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds
        self._max_tokens = max_tokens

    async def score(
        self,
        *,
        user_input: str,
        response: str,
        retrieved_contexts: Sequence[str],
    ) -> float:
        if self._provider != "openai" or not self._api_key:
            raise ValueError("RAGAS evaluation requires the configured OpenAI LLM provider.")
        from openai import AsyncOpenAI
        from ragas.llms import llm_factory
        from ragas.metrics.collections import Faithfulness

        client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=_normalized_base_url(self._base_url),
            timeout=self._timeout_seconds,
        )
        token_limit_kwargs: dict[str, Any] = _token_limit_kwargs(
            model=self._model,
            max_tokens=max(
                self._max_tokens,
                self._MIN_REASONING_MAX_TOKENS,
            ),
        )
        llm = llm_factory(
            self._model,
            client=client,
            **token_limit_kwargs,
        )
        scorer = Faithfulness(llm=llm)
        result = await asyncio.wait_for(
            scorer.ascore(
                user_input=user_input,
                response=response,
                retrieved_contexts=list(retrieved_contexts),
            ),
            timeout=self._timeout_seconds,
        )
        value = float(result.value)
        return round(max(0.0, min(1.0, value)) * 100.0, 2)


def _token_limit_kwargs(*, model: str, max_tokens: int) -> dict[str, int | str]:
    if model.startswith("gpt-5"):
        return {"max_completion_tokens": max_tokens, "reasoning_effort": "minimal"}
    return {"max_tokens": max_tokens}


def _normalized_base_url(base_url: str | None) -> str | None:
    return base_url or None
