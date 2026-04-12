from dataclasses import dataclass
from uuid import UUID

from researchlens.modules.retrieval.application.ports import (
    RetrievalIngestionRepository,
    SearchProvider,
)
from researchlens.modules.retrieval.application.retrieval_stage_steps import RetrievalStageSteps
from researchlens.modules.retrieval.domain.summary import RetrievalSummary
from researchlens.shared.config.embeddings import EmbeddingsSettings
from researchlens.shared.config.retrieval import RetrievalSettings
from researchlens.shared.embeddings.ports import EmbeddingClient
from researchlens.shared.llm.ports import StructuredGenerationClient


@dataclass(frozen=True, slots=True)
class RunRetrievalStageCommand:
    run_id: UUID
    research_question: str


class RunRetrievalStageUseCase:
    def __init__(
        self,
        *,
        settings: RetrievalSettings,
        primary_provider: SearchProvider,
        fallback_providers: tuple[SearchProvider, ...],
        ingestion_repository: RetrievalIngestionRepository | None = None,
        llm_client: StructuredGenerationClient | None = None,
        embedding_client: EmbeddingClient | None = None,
        embedding_settings: EmbeddingsSettings | None = None,
    ) -> None:
        self._steps = RetrievalStageSteps(
            settings=settings,
            primary_provider=primary_provider,
            fallback_providers=fallback_providers,
            ingestion_repository=ingestion_repository,
            llm_client=llm_client,
            embedding_client=embedding_client,
            embedding_settings=embedding_settings,
        )

    async def execute(self, command: RunRetrievalStageCommand) -> RetrievalSummary:
        planning = await self._steps.plan(question=command.research_question)
        selection = await self._steps.select_sources(
            query_plan=planning.query_plan,
            question=command.research_question,
        )
        return await self._steps.enrich_and_ingest(
            run_id=command.run_id,
            planning=planning,
            selection=selection,
        )
