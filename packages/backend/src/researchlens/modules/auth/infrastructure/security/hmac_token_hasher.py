import hmac
from hashlib import sha256


class HmacTokenHasher:
    def __init__(self, *, secret: str) -> None:
        self._secret = secret.encode("utf-8")

    def hash_token(self, token: str) -> str:
        return hmac.new(self._secret, token.encode("utf-8"), sha256).hexdigest()
