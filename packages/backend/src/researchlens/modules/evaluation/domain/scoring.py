from collections.abc import Iterable, Sequence

from researchlens.modules.evaluation.domain.claim_verdicts import ClaimVerdict

VERDICT_WEIGHTS: dict[ClaimVerdict, float] = {
    ClaimVerdict.SUPPORTED: 1.0,
    ClaimVerdict.MISSING_CITATION: 0.75,
    ClaimVerdict.INVALID_CITATION: 0.75,
    ClaimVerdict.OVERSTATED: 0.5,
    ClaimVerdict.UNSUPPORTED: 0.0,
    ClaimVerdict.CONTRADICTED: -1.0,
}


def section_quality(verdicts: Sequence[ClaimVerdict]) -> float:
    if not verdicts:
        return 0.0
    raw = sum(VERDICT_WEIGHTS[verdict] for verdict in verdicts) / len(verdicts)
    return _pct(max(raw, 0.0))


def report_quality(section_scores: Sequence[float]) -> float:
    if not section_scores:
        return 0.0
    return _pct(sum(section_scores) / len(section_scores) / 100.0)


def unsupported_claim_rate(verdicts: Iterable[ClaimVerdict]) -> float:
    items = tuple(verdicts)
    if not items:
        return 0.0
    unsupported = sum(
        1
        for verdict in items
        if verdict in {ClaimVerdict.UNSUPPORTED, ClaimVerdict.CONTRADICTED}
    )
    return _pct(unsupported / len(items))


def pass_rate(section_repair_recommendations: Sequence[bool]) -> float:
    if not section_repair_recommendations:
        return 0.0
    passing = sum(
        1 for repair_recommended in section_repair_recommendations if not repair_recommended
    )
    return _pct(passing / len(section_repair_recommendations))


def _pct(value: float) -> float:
    return round(max(0.0, min(100.0, value * 100.0)), 2)
