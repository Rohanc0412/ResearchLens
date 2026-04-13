import pytest
from pytest import MonkeyPatch

from researchlens.shared.config import InvalidSettingsError, get_settings
from researchlens.shared.config.app import AppSettings
from researchlens.shared.config.auth import AuthSettings
from researchlens.shared.config.bootstrap_actor import BootstrapActorSettings
from researchlens.shared.config.database import DatabaseSettings
from researchlens.shared.config.drafting import DraftingSettings
from researchlens.shared.config.embeddings import EmbeddingsSettings
from researchlens.shared.config.evaluation import EvaluationSettings
from researchlens.shared.config.llm import LlmSettings
from researchlens.shared.config.observability import ObservabilitySettings
from researchlens.shared.config.queue import QueueSettings
from researchlens.shared.config.repair import RepairSettings
from researchlens.shared.config.retrieval import RetrievalSettings
from researchlens.shared.config.settings_types import ResearchLensSettings
from researchlens.shared.config.smtp import SmtpSettings
from researchlens.shared.config.storage import StorageSettings
from researchlens.shared.config.validation import validate_settings


def test_settings_parse_grouped_environment(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./.data/test.db")
    monkeypatch.setenv("QUEUE_BACKEND", "redis")
    monkeypatch.setenv("QUEUE_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("STORAGE_MODE", "local")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "test-key")

    settings = get_settings()

    assert settings.app.environment == "test"
    assert settings.queue.backend == "redis"
    assert settings.storage.mode == "local"
    assert settings.llm.provider == "openai"


def test_settings_validation_rejects_insecure_production(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "production")

    with pytest.raises(InvalidSettingsError):
        get_settings()


def test_retrieval_validation_rejects_disabled_provider_set() -> None:
    settings = _settings(
        RetrievalSettings(enabled_providers=(), fallback_providers=()),
    )

    with pytest.raises(InvalidSettingsError, match="RETRIEVAL_ENABLED_PROVIDERS"):
        validate_settings(settings)


def test_retrieval_validation_rejects_primary_not_enabled() -> None:
    settings = _settings(
        RetrievalSettings(enabled_providers=("pubmed",), primary_provider="paper_search_mcp"),
    )

    with pytest.raises(InvalidSettingsError, match="RETRIEVAL_PRIMARY_PROVIDER"):
        validate_settings(settings)


def test_retrieval_validation_rejects_zero_ranking_weights() -> None:
    settings = _settings(
        RetrievalSettings(
            ranking_lexical_weight=0,
            ranking_embedding_weight=0,
            ranking_recency_weight=0,
            ranking_citation_weight=0,
        ),
    )

    with pytest.raises(InvalidSettingsError, match="ranking weights"):
        validate_settings(settings)


def test_drafting_validation_rejects_max_words_below_min_words() -> None:
    settings = _settings(
        RetrievalSettings(),
        DraftingSettings(section_min_words=200, section_max_words=100),
    )

    with pytest.raises(InvalidSettingsError, match="DRAFTING_SECTION_MAX_WORDS"):
        validate_settings(settings)


def _settings(
    retrieval: RetrievalSettings,
    drafting: DraftingSettings | None = None,
) -> ResearchLensSettings:
    return ResearchLensSettings(
        app=AppSettings(environment="test"),
        database=DatabaseSettings(url="sqlite+aiosqlite:///./.data/test.db"),
        bootstrap_actor=BootstrapActorSettings(),
        auth=AuthSettings(),
        smtp=SmtpSettings(),
        retrieval=retrieval,
        drafting=drafting or DraftingSettings(),
        evaluation=EvaluationSettings(),
        repair=RepairSettings(),
        llm=LlmSettings(),
        embeddings=EmbeddingsSettings(),
        observability=ObservabilitySettings(),
        queue=QueueSettings(),
        storage=StorageSettings(),
    )
