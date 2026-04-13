from typing import Protocol

REPAIR_FAITHFULNESS_THRESHOLD_PCT = 70.0
MAX_REPAIR_ATTEMPTS_PER_SECTION = 1


class RepairSelectionInput(Protocol):
    section_id: str
    section_order: int
    repair_attempt_count: int
    triggered_by_low_faithfulness: bool
    triggered_by_contradiction: bool


def section_is_repair_eligible(section: RepairSelectionInput) -> bool:
    return section.repair_attempt_count < MAX_REPAIR_ATTEMPTS_PER_SECTION and (
        section.triggered_by_low_faithfulness or section.triggered_by_contradiction
    )


def order_repair_inputs[RepairSelectionT: RepairSelectionInput](
    sections: tuple[RepairSelectionT, ...],
) -> tuple[RepairSelectionT, ...]:
    return tuple(sorted(sections, key=lambda item: (item.section_order, item.section_id)))


def select_repair_inputs[RepairSelectionT: RepairSelectionInput](
    sections: tuple[RepairSelectionT, ...],
) -> tuple[RepairSelectionT, ...]:
    ordered = order_repair_inputs(sections)
    return tuple(section for section in ordered if section_is_repair_eligible(section))
