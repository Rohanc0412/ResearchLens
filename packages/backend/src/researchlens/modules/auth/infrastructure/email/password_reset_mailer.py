from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PasswordResetMessage:
    email: str
    token: str


class CapturingPasswordResetMailer:
    def __init__(self) -> None:
        self.sent_messages: list[PasswordResetMessage] = []

    async def send_password_reset(self, *, email: str, token: str) -> None:
        self.sent_messages.append(PasswordResetMessage(email=email, token=token))
