import re

from researchlens.modules.repair.application.dtos import SectionRepairInput


def try_validated_fallback(repair_input: SectionRepairInput) -> tuple[str, str] | None:
    targets = tuple(
        issue.claim_text.strip()
        for issue in repair_input.issues
        if issue.verdict == "contradicted" and issue.claim_text and issue.claim_text.strip()
    )
    if not targets:
        return None
    revised = repair_input.current_section_text
    changed = False
    for target in targets:
        replacement = _remove_exact_sentence(text=revised, target=target)
        if replacement is None:
            return None
        revised = replacement
        changed = True
    if not changed or not revised.strip():
        return None
    return revised.strip(), repair_input.current_section_summary


def _remove_exact_sentence(*, text: str, target: str) -> str | None:
    pattern = re.compile(r"(?P<sentence>[^.!?\n]*" + re.escape(target) + r"[^.!?\n]*[.!?])")
    matches = tuple(pattern.finditer(text))
    if len(matches) != 1:
        if text.count(target) == 1:
            return text.replace(target, "").strip()
        return None
    sentence = matches[0].group("sentence")
    if sentence.count(target) != 1:
        return None
    return (text[: matches[0].start()] + text[matches[0].end() :]).strip()
