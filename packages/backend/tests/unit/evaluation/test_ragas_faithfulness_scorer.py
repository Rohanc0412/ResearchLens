from researchlens.modules.evaluation.infrastructure.ragas.faithfulness_scorer import (
    _normalized_base_url,
    _token_limit_kwargs,
)


def test_token_limit_kwargs_use_gpt5_chat_completion_parameter() -> None:
    assert _token_limit_kwargs(model="gpt-5-nano", max_tokens=8192) == {
        "max_completion_tokens": 8192,
        "reasoning_effort": "minimal",
    }


def test_token_limit_kwargs_keep_legacy_chat_completion_parameter() -> None:
    assert _token_limit_kwargs(model="gpt-4o-mini", max_tokens=4096) == {"max_tokens": 4096}


def test_normalized_base_url_treats_empty_string_as_default() -> None:
    assert _normalized_base_url("") is None
    assert _normalized_base_url(None) is None
    assert _normalized_base_url("https://example.test/v1") == "https://example.test/v1"
