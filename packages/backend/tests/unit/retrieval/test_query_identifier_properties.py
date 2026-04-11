from random import Random
from string import ascii_letters, digits

from researchlens.modules.retrieval.domain.candidate import CanonicalIdentifiers
from researchlens.modules.retrieval.domain.query_plan import normalize_query_intent


def test_query_intent_normalization_is_deterministic_for_generated_inputs() -> None:
    generator = Random(6)
    alphabet = ascii_letters + digits + " _-/.:;[]()"

    for _ in range(200):
        value = "".join(generator.choice(alphabet) for _ in range(generator.randint(0, 60)))
        assert normalize_query_intent(value) == normalize_query_intent(value)


def test_query_intent_normalization_emits_only_slug_characters_or_general() -> None:
    generator = Random(16)
    alphabet = ascii_letters + digits + " _-/.:;[]()"

    for _ in range(200):
        normalized = normalize_query_intent(
            "".join(generator.choice(alphabet) for _ in range(generator.randint(0, 60)))
        )
        assert normalized == "general" or all(
            character.islower() or character.isdigit() or character == "-"
            for character in normalized
        )


def test_canonical_identifier_normalization_is_stable_for_generated_inputs() -> None:
    generator = Random(26)

    for _ in range(200):
        raw_doi = f"  10.{generator.randint(1000, 9999)}/ABC-{generator.randint(1, 999)}  "
        identifiers = CanonicalIdentifiers(
            doi=raw_doi,
            pmid=f" {generator.randint(1, 999999)} ",
            pmcid=f" pmc{generator.randint(1, 999999)} ",
        )

        normalized = identifiers.normalized()

        assert normalized == normalized.normalized()
        assert normalized.doi == raw_doi.strip().casefold()
        assert normalized.pmid == identifiers.pmid.strip()
        assert normalized.pmcid == identifiers.pmcid.strip().upper()


def test_title_hash_fallback_is_stable_across_whitespace_and_case_variants() -> None:
    title = "Neural   Evidence   In Retrieval"
    identifiers = CanonicalIdentifiers()

    assert identifiers.canonical_key(title) == identifiers.canonical_key(
        " neural evidence in retrieval "
    )
