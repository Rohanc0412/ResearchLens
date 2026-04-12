import json
import random
from uuid import uuid4

import pytest

from researchlens.modules.drafting.application.run_drafting_stage import _normalize_structured_data
from researchlens.modules.drafting.domain import (
    ensure_only_valid_citation_tokens,
    parse_citation_tokens,
)
from researchlens.shared.errors import ValidationError


def test_normalize_structured_data_accepts_random_valid_json_payloads() -> None:
    random.seed(7)
    for _ in range(50):
        section_id = f"section-{random.randint(1, 999)}"
        token = uuid4()
        payload = {
            "section_id": section_id,
            "section_text": f"Grounded statement [[chunk:{token}]]",
            "section_summary": "Bridge only.",
            "status": "completed",
        }
        raw = json.dumps(payload)
        assert _normalize_structured_data({"raw": raw}) == payload


def test_citation_token_parser_rejects_random_malformed_tokens() -> None:
    random.seed(11)
    fragments = ["source", "bad", "evidence", "ref", "citation"]
    for _ in range(100):
        fragment = random.choice(fragments)
        text = f"Sentence [[{fragment}-{random.randint(1, 999)}]]"
        with pytest.raises(ValidationError):
            ensure_only_valid_citation_tokens(text)


def test_citation_token_parser_round_trips_random_valid_tokens() -> None:
    random.seed(13)
    for _ in range(50):
        tokens = tuple(uuid4() for _ in range(random.randint(1, 4)))
        text = " ".join(f"Claim [[chunk:{token}]]" for token in tokens)
        assert ensure_only_valid_citation_tokens(text) == tokens
        assert parse_citation_tokens(text) == tokens
