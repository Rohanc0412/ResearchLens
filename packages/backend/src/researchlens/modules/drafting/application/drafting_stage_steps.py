import asyncio
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import cast

from researchlens.modules.drafting.application.assembly import assemble_report
from researchlens.modules.drafting.application.briefs import (
    build_section_brief,
    to_allowed_evidence_item,
)
from researchlens.modules.drafting.application.dto import (
    EvidenceRecord,
    RunDraftingInput,
    SectionDraftPayload,
)
from researchlens.modules.drafting.application.ports import (
    DraftingGenerationClient,
    DraftingProgressSink,
    DraftingRepository,
    RunCancellationProbe,
)
from researchlens.modules.drafting.application.prompts import build_section_request
from researchlens.modules.drafting.application.validation import validate_section_payload
from researchlens.modules.drafting.domain import DraftingSection, EvidencePack, SectionBrief
from researchlens.shared.config.drafting import DraftingSettings
from researchlens.shared.errors import CancellationRequestedError, ValidationError


@dataclass(frozen=True, slots=True)
class DraftingPreparationResult:
    draft_input: RunDraftingInput
    briefs: tuple[SectionBrief, ...]


@dataclass(frozen=True, slots=True)
class DraftingRunResult:
    report_title: str
    section_count: int


class DraftingStageSteps:
    def __init__(
        self,
        *,
        settings: DraftingSettings,
        repository: DraftingRepository,
        generation_client: DraftingGenerationClient,
        cancellation_probe: RunCancellationProbe,
        provider_name: str,
    ) -> None:
        self._settings = settings
        self._repository = repository
        self._generation_client = generation_client
        self._cancellation_probe = cancellation_probe
        self._provider_name = provider_name

    async def prepare(
        self,
        *,
        draft_input: RunDraftingInput,
        progress: DraftingProgressSink | None = None,
    ) -> DraftingPreparationResult:
        if not draft_input.sections or not draft_input.evidence:
            raise ValidationError("Drafting requires persisted retrieval outputs before drafting.")
        briefs = await self._prepare_briefs(draft_input, progress=progress)
        await self._repository.replace_section_preparation(
            run_id=draft_input.run_id,
            briefs=briefs,
        )
        return DraftingPreparationResult(draft_input=draft_input, briefs=briefs)

    async def draft_sections(
        self,
        *,
        briefs: tuple[SectionBrief, ...],
        progress: DraftingProgressSink | None = None,
    ) -> None:
        semaphore = asyncio.Semaphore(self._settings.max_concurrent_section_drafts)
        persistence_semaphore = asyncio.Semaphore(
            min(self._settings.max_concurrent_section_persistence, 1)
        )
        tasks = [
            asyncio.create_task(
                self._draft_section(
                    brief=brief,
                    semaphore=semaphore,
                    persistence_semaphore=persistence_semaphore,
                    progress=progress,
                )
            )
            for brief in briefs
        ]
        await asyncio.gather(*tasks)

    async def assemble_report(
        self,
        *,
        draft_input: RunDraftingInput,
    ) -> DraftingRunResult:
        drafts = await self._repository.list_persisted_section_drafts(run_id=draft_input.run_id)
        report = assemble_report(
            run_id=draft_input.run_id,
            tenant_id=draft_input.tenant_id,
            report_title=draft_input.report_title,
            drafts=drafts,
        )
        await self._repository.replace_report_draft(draft=report)
        return DraftingRunResult(report_title=report.title, section_count=len(drafts))

    async def _prepare_briefs(
        self,
        draft_input: RunDraftingInput,
        *,
        progress: DraftingProgressSink | None,
    ) -> tuple[SectionBrief, ...]:
        section_map = {
            section.section_id: DraftingSection(
                run_id=draft_input.run_id,
                tenant_id=draft_input.tenant_id,
                section_id=section.section_id,
                title=section.title,
                section_order=section.section_order,
                goal=section.goal,
                key_points=section.key_points,
            )
            for section in draft_input.sections[: self._settings.max_sections_per_run]
        }
        grouped: dict[str, list[EvidenceRecord]] = defaultdict(list)
        for record in draft_input.evidence:
            key = record.target_section or "overview"
            if key in section_map:
                grouped[key].append(record)
        semaphore = asyncio.Semaphore(self._settings.max_concurrent_section_preparation)
        tasks = [
            asyncio.create_task(
                self._build_brief(
                    semaphore=semaphore,
                    report_title=draft_input.report_title,
                    section=section,
                    evidence_records=tuple(grouped.get(section.section_id, ())),
                    progress=progress,
                )
            )
            for section in sorted(section_map.values(), key=lambda item: item.section_order)
        ]
        return tuple(await asyncio.gather(*tasks))

    async def _build_brief(
        self,
        *,
        semaphore: asyncio.Semaphore,
        report_title: str,
        section: DraftingSection,
        evidence_records: tuple[EvidenceRecord, ...],
        progress: DraftingProgressSink | None,
    ) -> SectionBrief:
        async with semaphore:
            if not evidence_records:
                raise ValidationError(f"Section '{section.section_id}' has no eligible evidence.")
            items = tuple(
                to_allowed_evidence_item(
                    tenant_id=record.tenant_id,
                    run_id=record.run_id,
                    source_id=record.source_id,
                    chunk_id=record.chunk_id,
                    source_rank=record.source_rank,
                    chunk_index=record.chunk_index,
                    title=record.source_title,
                    excerpt=record.chunk_text[: self._settings.max_evidence_chars_per_item],
                )
                for record in sorted(
                    evidence_records,
                    key=lambda item: (item.source_rank, item.chunk_index, str(item.chunk_id)),
                )[: self._settings.max_evidence_items_per_section]
            )
            brief = build_section_brief(
                report_title=report_title,
                section=section,
                evidence_pack=EvidencePack(
                    tenant_id=section.tenant_id,
                    run_id=section.run_id,
                    section_id=section.section_id,
                    items=items,
                ),
                prior_continuity_summary=None,
            )
            if progress is not None:
                await progress.evidence_pack_ready(
                    section_id=section.section_id,
                    evidence_count=len(brief.evidence_pack.items),
                )
            return brief

    async def _draft_section(
        self,
        *,
        brief: SectionBrief,
        semaphore: asyncio.Semaphore,
        persistence_semaphore: asyncio.Semaphore,
        progress: DraftingProgressSink | None,
    ) -> None:
        async with semaphore:
            if await self._cancellation_probe.cancel_requested(run_id=brief.section.run_id):
                raise CancellationRequestedError("Drafting canceled before section generation.")
            if progress is not None:
                await progress.section_started(section_id=brief.section.section_id)
            error_message = ""
            for attempt in range(self._settings.correction_retry_count + 1):
                request = build_section_request(
                    brief,
                    min_words=self._settings.section_min_words,
                    max_words=self._settings.section_max_words,
                    max_output_tokens=self._settings.section_max_output_tokens,
                )
                if error_message:
                    request = request.__class__(
                        schema_name=request.schema_name,
                        system_prompt=request.system_prompt,
                        max_output_tokens=request.max_output_tokens,
                        prompt=f"{request.prompt}\n\nCorrect the previous issue: {error_message}",
                    )
                result = await self._generation_client.generate_structured(request)
                try:
                    payload = SectionDraftPayload.model_validate(
                        _normalize_structured_data(result.data)
                    )
                    draft = validate_section_payload(
                        payload=payload,
                        section=brief.section,
                        evidence_pack=brief.evidence_pack,
                        provider_name=self._provider_name,
                        model_name=self._generation_client.model,
                    )
                    async with persistence_semaphore:
                        await self._repository.replace_section_draft(draft=draft)
                    if progress is not None:
                        await progress.section_completed(section_id=brief.section.section_id)
                    return
                except Exception as exc:
                    error_message = str(exc)
                    if progress is not None and attempt < self._settings.correction_retry_count:
                        await progress.correction_retry(
                            section_id=brief.section.section_id,
                            reason=error_message,
                            attempt=attempt + 1,
                        )
                    if attempt >= self._settings.correction_retry_count:
                        raise
            raise RuntimeError("Drafting retry loop terminated unexpectedly.")


def _normalize_structured_data(data: dict[str, object]) -> dict[str, object]:
    if data.keys() >= {"section_id", "section_text", "section_summary", "status"}:
        return data
    raw = data.get("raw")
    if isinstance(raw, str):
        loaded = json.loads(raw)
        return cast(dict[str, object], loaded) if isinstance(loaded, dict) else data
    return data
