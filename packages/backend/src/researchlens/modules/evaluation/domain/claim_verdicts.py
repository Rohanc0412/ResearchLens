from enum import StrEnum


class ClaimVerdict(StrEnum):
    SUPPORTED = "supported"
    MISSING_CITATION = "missing_citation"
    INVALID_CITATION = "invalid_citation"
    OVERSTATED = "overstated"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"
