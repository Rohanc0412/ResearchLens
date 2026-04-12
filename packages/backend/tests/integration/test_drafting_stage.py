import asyncio
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.drafting.infrastructure import (
    SqlAlchemyDraftingRepository,
    SqlAlchemyDraftingRunInputReader,
)
from researchlens.modules.drafting.infrastructure.rows import (
    DraftingReportDraftRow,
    DraftingSectionDraftRow,
    DraftingSectionEvidenceRow,
    DraftingSectionRow,
)
from researchlens.modules.drafting.orchestration import DraftingStageOrchestrator
from researchlens.shared.config import get_settings, reset_settings_cache
from researchlens.shared.db import DatabaseRuntime
from researchlens.shared.errors import ValidationError

from .drafting_support import FakeDraftingClient, seed_run_with_retrieval_outputs


class _NoopEventWriter:
    async def info(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        return None

    async def warning(self, *, key: str, message: str, payload: dict[str, object]) -> None:
        return None


class _NoopCheckpointWriter:
    async def checkpoint(self, *, key: str, summary: dict[str, object]) -> None:
        return None


class _SessionCancellationProbe:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def cancel_requested(self, *, run_id: UUID) -> bool:
        return False


@pytest.mark.asyncio
async def test_drafting_stage_persists_sections_evidence_and_report(
    database_runtime: DatabaseRuntime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    reset_settings_cache()
    async with database_runtime.session_factory() as session:
        _, run_id = await seed_run_with_retrieval_outputs(
            session,
            section_ids=("overview", "risks"),
        )

    async with database_runtime.session_factory() as session:
        orchestrator = DraftingStageOrchestrator(
            settings=get_settings(),
            input_reader=SqlAlchemyDraftingRunInputReader(session),
            repository=SqlAlchemyDraftingRepository(session),
            cancellation_probe=_SessionCancellationProbe(session),
            generation_client=FakeDraftingClient(),
        )
        await orchestrator.execute(
            run_id=run_id,
            events=_NoopEventWriter(),
            checkpoints=_NoopCheckpointWriter(),
        )
        await session.commit()

    async with database_runtime.session_factory() as session:
        section_count = await session.scalar(
            select(func.count())
            .select_from(DraftingSectionRow)
            .where(DraftingSectionRow.run_id == run_id)
        )
        evidence_count = await session.scalar(
            select(func.count())
            .select_from(DraftingSectionEvidenceRow)
            .where(DraftingSectionEvidenceRow.run_id == run_id)
        )
        draft_count = await session.scalar(
            select(func.count())
            .select_from(DraftingSectionDraftRow)
            .where(DraftingSectionDraftRow.run_id == run_id)
        )
        report = await session.scalar(
            select(DraftingReportDraftRow).where(DraftingReportDraftRow.run_id == run_id)
        )

    assert section_count == 2
    assert evidence_count == 2
    assert draft_count == 2
    assert report is not None
    assert report.markdown_text.startswith("# What is the state of AI safety benchmarking?")


@pytest.mark.asyncio
async def test_drafting_stage_fails_when_a_section_has_no_evidence(
    database_runtime: DatabaseRuntime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    reset_settings_cache()
    async with database_runtime.session_factory() as session:
        _, run_id = await seed_run_with_retrieval_outputs(session, section_ids=())

    async with database_runtime.session_factory() as session:
        with pytest.raises(ValidationError):
            await DraftingStageOrchestrator(
                settings=get_settings(),
                input_reader=SqlAlchemyDraftingRunInputReader(session),
                repository=SqlAlchemyDraftingRepository(session),
                cancellation_probe=_SessionCancellationProbe(session),
                generation_client=FakeDraftingClient(),
            ).execute(
                run_id=run_id,
                events=_NoopEventWriter(),
                checkpoints=_NoopCheckpointWriter(),
            )


@pytest.mark.asyncio
async def test_drafting_stage_retries_on_malformed_and_invalid_citations(
    database_runtime: DatabaseRuntime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    reset_settings_cache()
    async with database_runtime.session_factory() as session:
        _, run_id = await seed_run_with_retrieval_outputs(
            session,
            section_ids=("overview", "risks"),
        )

    async with database_runtime.session_factory() as session:
        orchestrator = DraftingStageOrchestrator(
            settings=get_settings(),
            input_reader=SqlAlchemyDraftingRunInputReader(session),
            repository=SqlAlchemyDraftingRepository(session),
            cancellation_probe=_SessionCancellationProbe(session),
            generation_client=FakeDraftingClient(
                malformed_once_for={"overview"},
                invalid_once_for={"risks"},
            ),
        )
        await orchestrator.execute(
            run_id=run_id,
            events=_NoopEventWriter(),
            checkpoints=_NoopCheckpointWriter(),
        )
        await session.commit()

    async with database_runtime.session_factory() as session:
        drafts = (
            await session.scalars(
                select(DraftingSectionDraftRow).where(DraftingSectionDraftRow.run_id == run_id)
            )
        ).all()

    assert len(drafts) == 2
    assert all("[[chunk:" in draft.section_text for draft in drafts)


@pytest.mark.asyncio
async def test_drafting_stage_drafts_sections_concurrently(
    database_runtime: DatabaseRuntime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    reset_settings_cache()
    wait_event = asyncio.Event()
    release_event = asyncio.Event()
    async with database_runtime.session_factory() as session:
        _, run_id = await seed_run_with_retrieval_outputs(
            session,
            section_ids=("overview", "risks", "gaps"),
        )

    async with database_runtime.session_factory() as session:
        client = FakeDraftingClient(wait_event=wait_event, release_event=release_event)
        orchestrator = DraftingStageOrchestrator(
            settings=get_settings(),
            input_reader=SqlAlchemyDraftingRunInputReader(session),
            repository=SqlAlchemyDraftingRepository(session),
            cancellation_probe=_SessionCancellationProbe(session),
            generation_client=client,
        )
        task = asyncio.create_task(
            orchestrator.execute(
                run_id=run_id,
                events=_NoopEventWriter(),
                checkpoints=_NoopCheckpointWriter(),
            )
        )
        await wait_event.wait()
        await asyncio.sleep(0.05)
        release_event.set()
        await task

    assert client.max_active_calls > 1
