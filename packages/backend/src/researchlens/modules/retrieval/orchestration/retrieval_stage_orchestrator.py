from dataclasses import asdict
from typing import Protocol
from uuid import UUID

from researchlens.modules.retrieval.application.ports import RetrievalIngestionRepository
from researchlens.modules.retrieval.application.run_retrieval_stage import (
    RunRetrievalStageCommand,
    RunRetrievalStageUseCase,
)
from researchlens.modules.retrieval.infrastructure.providers.provider_registry import (
    build_provider_registry,
)
from researchlens.shared.config import ResearchLensSettings
from researchlens.shared.embeddings.factory import build_embedding_client
from researchlens.shared.embeddings.ports import EmbeddingClient
from researchlens.shared.llm.factory import build_llm_client
from researchlens.shared.llm.ports import StructuredGenerationClient


class RetrievalStageEventWriter(Protocol):
    async def info(self, *, key: str, message: str, payload: dict[str, object]) -> None: ...

    async def warning(self, *, key: str, message: str, payload: dict[str, object]) -> None: ...


class RetrievalStageCheckpointWriter(Protocol):
    async def checkpoint(self, *, key: str, summary: dict[str, object]) -> None: ...


class RetrievalStageOrchestrator:
    def __init__(
        self,
        *,
        settings: ResearchLensSettings,
        ingestion_repository: RetrievalIngestionRepository | None = None,
        llm_client: StructuredGenerationClient | None = None,
        embedding_client: EmbeddingClient | None = None,
    ) -> None:
        retrieval_settings = settings.retrieval
        providers = build_provider_registry(retrieval_settings)
        primary = providers[retrieval_settings.primary_provider]
        fallback = tuple(
            provider
            for name, provider in providers.items()
            if name in retrieval_settings.fallback_providers
        )
        self._use_case = RunRetrievalStageUseCase(
            settings=retrieval_settings,
            primary_provider=primary,
            fallback_providers=fallback,
            ingestion_repository=ingestion_repository,
            llm_client=llm_client or _configured_llm(settings),
            embedding_client=embedding_client or _configured_embedding(settings),
            embedding_settings=settings.embeddings,
        )

    async def execute(
        self,
        *,
        run_id: UUID,
        research_question: str,
        events: RetrievalStageEventWriter,
        checkpoints: RetrievalStageCheckpointWriter,
    ) -> None:
        await events.info(
            key="retrieval:outline-started",
            message="Retrieval outline generation started",
            payload={},
        )
        await events.info(
            key="retrieval:query-planning-started",
            message="Retrieval query planning started",
            payload={},
        )
        result = await self._use_case.execute(
            RunRetrievalStageCommand(run_id=run_id, research_question=research_question)
        )
        payload = asdict(result)
        payload["run_id"] = str(result.run_id)
        if result.fallback_used:
            await events.warning(
                key="retrieval:provider-fallback-used",
                message="Direct provider fallback was used",
                payload={"reason": "primary yielded too few normalized candidates"},
            )
        if result.provider_failures:
            await events.warning(
                key="retrieval:provider-failures",
                message="One or more retrieval providers failed",
                payload={"providers": list(result.provider_failures)},
            )
        if result.planning_warnings:
            await events.warning(
                key="retrieval:planning-fallbacks",
                message="Retrieval planning used fallback behavior",
                payload={"warnings": list(result.planning_warnings)},
            )
        await checkpoints.checkpoint(key="retrieval:summary", summary=payload)
        await events.info(
            key="retrieval:summary-completed",
            message="Retrieval summary completed",
            payload=payload,
        )


def _configured_llm(settings: ResearchLensSettings) -> StructuredGenerationClient | None:
    if settings.llm.provider == "disabled" or not settings.llm.api_key:
        return None
    return build_llm_client(settings.llm)


def _configured_embedding(settings: ResearchLensSettings) -> EmbeddingClient | None:
    if settings.embeddings.provider == "disabled" or not settings.embeddings.api_key:
        return None
    return build_embedding_client(settings.embeddings)
