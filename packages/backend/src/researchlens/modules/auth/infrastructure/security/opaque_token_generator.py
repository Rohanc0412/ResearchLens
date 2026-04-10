import secrets


class OpaqueTokenGenerator:
    def generate(self) -> str:
        return secrets.token_urlsafe(48)
