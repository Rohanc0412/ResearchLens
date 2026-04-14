from types import SimpleNamespace
from typing import Any, cast

import pytest

from researchlens.modules.evaluation.infrastructure.ragas.faithfulness_scorer import (
    RagasFaithfulnessScorer,
)


@pytest.mark.asyncio
async def test_ragas_faithfulness_scorer_uses_reasoning_safe_token_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    def fake_llm_factory(model: str, **kwargs: object) -> object:
        seen["model"] = model
        seen["kwargs"] = kwargs
        return object()

    class FakeFaithfulness:
        def __init__(self, *, llm: object) -> None:
            seen["llm"] = llm

        async def ascore(
            self,
            *,
            user_input: str,
            response: str,
            retrieved_contexts: list[str],
        ) -> object:
            seen["sample"] = (user_input, response, retrieved_contexts)
            return SimpleNamespace(value=0.75)

    monkeypatch.setattr("ragas.llms.llm_factory", fake_llm_factory)
    monkeypatch.setattr("ragas.metrics.collections.Faithfulness", FakeFaithfulness)

    score = await RagasFaithfulnessScorer(
        provider="openai",
        model="gpt-5-nano",
        api_key="test-key",
        base_url="https://api.openai.test/v1",
        timeout_seconds=30.0,
        max_tokens=15000,
    ).score(
        user_input="Question",
        response="Answer",
        retrieved_contexts=("Context",),
    )

    assert score == 75.0
    assert seen["model"] == "gpt-5-nano"
    assert seen["sample"] == ("Question", "Answer", ["Context"])
    kwargs = cast(dict[str, Any], seen["kwargs"])
    assert kwargs["max_tokens"] == 15000
