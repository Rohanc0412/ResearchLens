from enum import StrEnum


class EvaluationIssueType(StrEnum):
    MISSING_CITATION = "missing_citation"
    INVALID_CITATION = "invalid_citation"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    CONTRADICTED_CLAIM = "contradicted_claim"
    OVERSTATED_CLAIM = "overstated_claim"
    EMPTY_SECTION_EVIDENCE = "empty_section_evidence"
    EMPTY_SECTION_TEXT = "empty_section_text"
    EVALUATION_PROVIDER_FAILURE = "evaluation_provider_failure"
