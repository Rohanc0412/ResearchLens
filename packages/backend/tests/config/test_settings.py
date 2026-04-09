import pytest
from pytest import MonkeyPatch

from researchlens.shared.config import InvalidSettingsError, get_settings


def test_settings_parse_grouped_environment(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./.data/test.db")
    monkeypatch.setenv("QUEUE_BACKEND", "redis")
    monkeypatch.setenv("QUEUE_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("STORAGE_MODE", "s3")
    monkeypatch.setenv("STORAGE_BUCKET", "researchlens-test")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "test-key")

    settings = get_settings()

    assert settings.app.environment == "test"
    assert settings.queue.backend == "redis"
    assert settings.storage.bucket == "researchlens-test"
    assert settings.llm.provider == "openai"


def test_settings_validation_rejects_insecure_production(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "production")

    with pytest.raises(InvalidSettingsError):
        get_settings()
