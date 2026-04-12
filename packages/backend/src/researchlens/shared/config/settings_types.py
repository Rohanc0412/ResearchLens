from pydantic import BaseModel

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
from researchlens.shared.config.smtp import SmtpSettings
from researchlens.shared.config.storage import StorageSettings


class ResearchLensSettings(BaseModel):
    app: AppSettings
    database: DatabaseSettings
    bootstrap_actor: BootstrapActorSettings
    auth: AuthSettings
    smtp: SmtpSettings
    retrieval: RetrievalSettings
    drafting: DraftingSettings
    llm: LlmSettings
    embeddings: EmbeddingsSettings
    observability: ObservabilitySettings
    queue: QueueSettings
    storage: StorageSettings
