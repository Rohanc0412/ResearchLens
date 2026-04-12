from collections.abc import Iterable

from researchlens.modules.evaluation.domain.claim_verdicts import ClaimVerdict

REPAIR_FAITHFULNESS_THRESHOLD_PCT = 70.0
MAX_REPAIRS_PER_SECTION = 1


def section_requires_repair(
    *,
    ragas_faithfulness_pct: float,
    verdicts: Iterable[ClaimVerdict],
) -> bool:
    return ragas_faithfulness_pct < REPAIR_FAITHFULNESS_THRESHOLD_PCT or any(
        verdict == ClaimVerdict.CONTRADICTED for verdict in verdicts
    )
