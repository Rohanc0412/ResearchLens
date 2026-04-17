import asyncio
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from researchlens.shared.errors import InfrastructureError

logger = logging.getLogger(__name__)

_SMTP_TIMEOUT_SECONDS = 10


class SmtpPasswordResetMailer:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        starttls: bool,
        from_name: str,
        from_email: str,
        password_reset_minutes: int,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._starttls = starttls
        self._from_name = from_name
        self._from_email = from_email
        self._password_reset_minutes = password_reset_minutes

    async def send_password_reset(self, *, email: str, token: str) -> None:
        message = self._build_message(email=email, token=token)
        try:
            await asyncio.to_thread(self._send_message, message)
        except Exception as exc:
            logger.exception("password reset email delivery failed")
            raise InfrastructureError("Password reset email delivery failed.") from exc

    def _build_message(self, *, email: str, token: str) -> EmailMessage:
        message = EmailMessage()
        message["Subject"] = "ResearchLens password reset code"
        message["From"] = formataddr((self._from_name, self._from_email))
        message["To"] = email
        message.set_content(
            "\n".join(
                [
                    "Use this ResearchLens password reset code to continue:",
                    "",
                    token,
                    "",
                    f"This code expires in {self._password_reset_minutes} minutes.",
                    "If you did not request a password reset, you can ignore this email.",
                ]
            )
        )
        return message

    def _send_message(self, message: EmailMessage) -> None:
        with smtplib.SMTP(self._host, self._port, timeout=_SMTP_TIMEOUT_SECONDS) as client:
            client.ehlo()
            if self._starttls:
                client.starttls(context=ssl.create_default_context())
                client.ehlo()
            if self._username and self._password:
                client.login(self._username, self._password)
            client.send_message(message)

