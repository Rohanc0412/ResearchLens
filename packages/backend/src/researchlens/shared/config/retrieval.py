from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RetrievalSettings(BaseSettings):
    enabled: bool = True
    enabled_providers: tuple[str, ...] = (
        "paper_search_mcp",
        "pubmed",
        "europe_pmc",
        "openalex",
        "arxiv",
    )
    primary_provider: str = "paper_search_mcp"
    fallback_providers: tuple[str, ...] = ("pubmed", "europe_pmc", "openalex", "arxiv")
    fallback_threshold: int = Field(default=5, ge=1)
    max_sources_per_run: int = Field(default=20, ge=1)
    allow_external_fetch: bool = False
    max_outline_sections: int = Field(default=6, ge=1)
    max_global_queries: int = Field(default=3, ge=1)
    max_queries_per_section: int = Field(default=2, ge=1)
    max_global_queries_total: int = Field(default=20, ge=1)
    max_results_per_provider_query: int = Field(default=10, ge=1)
    max_candidates_after_normalization: int = Field(default=200, ge=1)
    max_candidates_sent_to_rerank: int = Field(default=60, ge=1)
    min_selected_sources: int = Field(default=5, ge=1)
    max_selected_sources: int = Field(default=20, ge=1)
    max_concurrent_provider_searches: int = Field(default=12, ge=1)
    max_concurrent_enrichment_fetches: int = Field(default=8, ge=1)
    provider_timeout_seconds: float = Field(default=20.0, gt=0)
    stage_soft_time_budget_seconds: float = Field(default=170.0, gt=0)
    ranking_lexical_weight: float = Field(default=1.0, ge=0.0)
    ranking_embedding_weight: float = Field(default=0.7, ge=0.0)
    ranking_recency_weight: float = Field(default=0.2, ge=0.0)
    ranking_citation_weight: float = Field(default=0.3, ge=0.0)
    diversity_per_bucket_limit: int = Field(default=3, ge=1)
    ingestion_chunk_size: int = Field(default=2000, ge=100)
    ingestion_chunk_overlap: int = Field(default=200, ge=0)

    @field_validator("fallback_providers", "enabled_providers", mode="before")
    @classmethod
    def _split_provider_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(item.strip() for item in value.split(",") if item.strip())
        return value

    model_config = SettingsConfigDict(
        env_prefix="RETRIEVAL_",
        extra="ignore",
    )
