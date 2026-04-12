import asyncio
from collections.abc import Sequence


class RagasFaithfulnessScorer:
    def __init__(
        self,
        *,
        provider: str,
        model: str,
        api_key: str | None,
        base_url: str | None,
        timeout_seconds: float,
    ) -> None:
        self._provider = provider
        self._model = model
        self._api_key = api_key
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds

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

        client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
        llm = llm_factory(self._model, client=client)
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
