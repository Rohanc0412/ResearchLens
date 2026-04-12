from functools import lru_cache

from researchlens.shared.config.app import AppSettings
from researchlens.shared.config.auth import AuthSettings
from researchlens.shared.config.bootstrap_actor import BootstrapActorSettings
from researchlens.shared.config.database import DatabaseSettings
from researchlens.shared.config.drafting import DraftingSettings
from researchlens.shared.config.embeddings import EmbeddingsSettings
from researchlens.shared.config.llm import LlmSettings
from researchlens.shared.config.observability import ObservabilitySettings
from researchlens.shared.config.queue import QueueSettings
from researchlens.shared.config.retrieval import RetrievalSettings
from researchlens.shared.config.settings_types import ResearchLensSettings
from researchlens.shared.config.smtp import SmtpSettings
from researchlens.shared.config.storage import StorageSettings
from researchlens.shared.config.validation import validate_settings


def load_settings() -> ResearchLensSettings:
    settings = ResearchLensSettings(
        app=AppSettings(),
        database=DatabaseSettings(),
        bootstrap_actor=BootstrapActorSettings(),
        auth=AuthSettings(),
        smtp=SmtpSettings(),
        retrieval=RetrievalSettings(),
        drafting=DraftingSettings(),
        llm=LlmSettings(),
        embeddings=EmbeddingsSettings(),
        observability=ObservabilitySettings(),
        queue=QueueSettings(),
        storage=StorageSettings(),
    )
    validate_settings(settings)
    return settings


@lru_cache(maxsize=1)
def get_settings() -> ResearchLensSettings:
    return load_settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
