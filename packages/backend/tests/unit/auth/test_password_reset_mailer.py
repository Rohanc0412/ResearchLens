import asyncio
from typing import Any, cast

import researchlens.modules.auth.infrastructure.email.smtp_password_reset_mailer as smtp_mailer_module
from researchlens.modules.auth.infrastructure.email import (
    CapturingPasswordResetMailer,
    SmtpPasswordResetMailer,
)
from researchlens.modules.auth.infrastructure.runtime import SqlAlchemyAuthRuntime
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


def test_auth_runtime_uses_capture_mailer_when_smtp_is_disabled() -> None:
    runtime = SqlAlchemyAuthRuntime(
        session_factory=cast(Any, None),
        settings=_settings(),
    )

    assert isinstance(runtime.password_reset_mailer, CapturingPasswordResetMailer)


def test_auth_runtime_uses_smtp_mailer_when_smtp_is_enabled() -> None:
    runtime = SqlAlchemyAuthRuntime(
        session_factory=cast(Any, None),
        settings=_settings(
            smtp=SmtpSettings(
                enabled=True,
                host="smtp.example.com",
                username="mailer",
                password="secret",
            )
        ),
    )

    assert isinstance(runtime.password_reset_mailer, SmtpPasswordResetMailer)


def test_smtp_mailer_sends_password_reset_email(monkeypatch) -> None:
    sent_messages: list[Any] = []

    class FakeSmtpClient:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            self.host = host
            self.port = port
            self.timeout = timeout
            self.logged_in: tuple[str, str] | None = None
            self.starttls_called = False

        def __enter__(self) -> "FakeSmtpClient":
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            return None

        def ehlo(self) -> None:
            return None

        def starttls(self, *, context) -> None:
            self.starttls_called = True

        def login(self, username: str, password: str) -> None:
            self.logged_in = (username, password)

        def send_message(self, message) -> None:
            sent_messages.append(
                {
                    "client": self,
                    "message": message,
                }
            )

    monkeypatch.setattr(smtp_mailer_module.smtplib, "SMTP", FakeSmtpClient)

    mailer = SmtpPasswordResetMailer(
        host="smtp.example.com",
        port=587,
        username="mailer",
        password="secret",
        starttls=True,
        from_name="ResearchLens",
        from_email="noreply@example.com",
        password_reset_minutes=30,
    )

    asyncio.run(mailer.send_password_reset(email="casey@example.com", token="ABC123"))

    assert len(sent_messages) == 1
    smtp_call = sent_messages[0]
    message = smtp_call["message"]

    assert smtp_call["client"].host == "smtp.example.com"
    assert smtp_call["client"].port == 587
    assert smtp_call["client"].timeout == 10
    assert smtp_call["client"].starttls_called is True
    assert smtp_call["client"].logged_in == ("mailer", "secret")
    assert message["To"] == "casey@example.com"
    assert message["Subject"] == "ResearchLens password reset code"
    assert "ABC123" in message.get_content()
    assert "30 minutes" in message.get_content()


def _settings(
    *,
    smtp: SmtpSettings | None = None,
) -> ResearchLensSettings:
    return ResearchLensSettings(
        app=AppSettings(environment="test"),
        database=DatabaseSettings(url="sqlite+aiosqlite:///./.data/test.db"),
        bootstrap_actor=BootstrapActorSettings(),
        auth=AuthSettings(),
        smtp=smtp or SmtpSettings(),
        retrieval=RetrievalSettings(),
        drafting=DraftingSettings(),
        evaluation=EvaluationSettings(),
        repair=RepairSettings(),
        llm=LlmSettings(),
        embeddings=EmbeddingsSettings(),
        observability=ObservabilitySettings(),
        queue=QueueSettings(),
        storage=StorageSettings(),
    )
